# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import datetime
import logging
_logger = logging.getLogger(__name__)

class TestPosTimesheet(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        _logger.info("========== START setUpClass ==========")

        # Handle Odoo 19 specific partner constraints
        cls.env['ir.default'].set(
            'res.partner',
            'autopost_bills',
            'never'
        )

        _logger.info(
            "Configured default autopost_bills for res.partner"
        )

        cls.company = cls.env.user.company_id

        _logger.info(
            "Using Company: %s (ID: %s)",
            cls.company.name,
            cls.company.id
        )

        # ---------------------------------------------------------
        # Setup Analytic Plan
        # ---------------------------------------------------------
        cls.analytic_plan = cls.env[
            'account.analytic.plan'
        ].search([], limit=1)

        _logger.info(
            "Using Analytic Plan: %s (ID: %s)",
            cls.analytic_plan.name,
            cls.analytic_plan.id
        )

        # ---------------------------------------------------------
        # Setup Analytic Account
        # ---------------------------------------------------------
        cls.analytic_account = cls.env[
            'account.analytic.account'
        ].create({
            'name': 'Test Analytic Account',
            'plan_id': cls.analytic_plan.id,
        })

        _logger.info(
            "Created Analytic Account: %s (ID: %s)",
            cls.analytic_account.name,
            cls.analytic_account.id
        )

        # ---------------------------------------------------------
        # Setup Project
        # ---------------------------------------------------------
        cls.project = cls.env['project.project'].create({
            'name': 'POS Timesheet Project',
            'allow_timesheets': True,
            'account_id': cls.analytic_account.id,
        })

        _logger.info(
            "Created Project: %s (ID: %s)",
            cls.project.name,
            cls.project.id
        )

        # ---------------------------------------------------------
        # Setup Employee
        # ---------------------------------------------------------
        cls.employee = cls.env['hr.employee'].create({
            'name': 'POS Cashier Employee',
        })

        _logger.info(
            "Created Employee: %s (ID: %s)",
            cls.employee.name,
            cls.employee.id
        )

        # ---------------------------------------------------------
        # Setup POS Config
        # ---------------------------------------------------------
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'POS timesheet config',
            'module_pos_hr': True,
            'time_log': True,
            'project_id': cls.project.id,
        })

        _logger.info(
            "Created POS Config: %s (ID: %s)",
            cls.pos_config.name,
            cls.pos_config.id
        )

        _logger.info("========== SUCCESS setUpClass ==========")

    def test_01_pos_session_project_validation(self):
        """Test that ValidationError is raised when project settings are invalid or missing."""
        # 1. Test missing project
        config_no_project = self.env['pos.config'].create({
            'name': 'No Project Config',
            'module_pos_hr': True,
            'time_log': True,
        })
        with self.assertRaises(ValidationError, msg="Should raise ValidationError if project is not set on config"):
            self.env['pos.session'].create({
                'config_id': config_no_project.id,
            })

        # 2. Test project with allow_timesheets = False
        project_no_timesheet = self.env['project.project'].create({
            'name': 'No Timesheet Project',
            'allow_timesheets': False,
        })
        config_bad_project = self.env['pos.config'].create({
            'name': 'Bad Project Config',
            'module_pos_hr': True,
            'time_log': True,
            'project_id': project_no_timesheet.id,
        })
        with self.assertRaises(ValidationError, msg="Should raise ValidationError if project has timesheets disabled"):
            self.env['pos.session'].create({
                'config_id': config_bad_project.id,
            })

    def test_02_pos_session_creation_flow(self):
        """Test successful session creation, task creation, and sequence generation."""

        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })

        # Check sequence allocation
        self.assertTrue(session.project_sequence_number > 0)
        self.assertTrue(session.time_log_sequence_number > 0)

        # Check task was created and mapped correctly
        self.assertTrue(session.task_id)
        self.assertEqual(session.task_id.pos_session_id, session)
        self.assertEqual(session.task_id.project_id, self.project)
        self.assertEqual(session.task_id.company_id, self.pos_config.company_id)

        # Check naming functions
        expected_project_name = f"{self.project.display_name}/{session.project_sequence_number:05d}"
        self.assertEqual(session._get_project_session_name(), expected_project_name)

        expected_task_name = f"{self.pos_config.display_name}/{session.time_log_sequence_number:05d}"
        self.assertEqual(session._get_time_log_task_name(), expected_task_name)

    def test_03_set_timesheet_creation_and_update(self):
        """Test creating and then updating timesheet entries (account.analytic.line) via session set_timesheet."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })

        # Let's send 120 minutes (2 hours) of check in time
        # timestamp: May 19, 2026 10:00:00 (1779184800000 ms)
        check_in_timestamp = 1779184800000 
        check_in_date = datetime.datetime.fromtimestamp(check_in_timestamp / 1000).date()

        timesheet_data = [{
            'workMinutes': 120,
            'sessionId': session.id,
            'cashierId': self.employee.id,
            'checkInTime': check_in_timestamp,
        }]

        # Create Timesheet Line
        res = session.set_timesheet(timesheet_data)
        self.assertTrue(res)

        # Verify analytic line creation
        timesheet_line = self.env['account.analytic.line'].search([
            ('task_id', '=', session.task_id.id),
            ('employee_id', '=', self.employee.id),
            ('date', '=', check_in_date)
        ])
        self.assertEqual(len(timesheet_line), 1)
        self.assertEqual(timesheet_line.unit_amount, 2.0)
        self.assertEqual(timesheet_line.project_id, self.project)
        self.assertEqual(timesheet_line.account_id, self.project.account_id)
        self.assertEqual(timesheet_line.name, f"{session.name} - {session.task_id.name}")

        # Update the same timesheet line by sending another 60 minutes (1 hour)
        update_data = [{
            'workMinutes': 60,
            'sessionId': session.id,
            'cashierId': self.employee.id,
            'checkInTime': check_in_timestamp,
        }]
        res_update = session.set_timesheet(update_data)
        self.assertTrue(res_update)

        # Verify it updated the existing line to 3.0 hours instead of creating a new line
        updated_timesheet_lines = self.env['account.analytic.line'].search([
            ('task_id', '=', session.task_id.id),
            ('employee_id', '=', self.employee.id),
            ('date', '=', check_in_date)
        ])
        self.assertEqual(len(updated_timesheet_lines), 1)
        self.assertEqual(updated_timesheet_lines.unit_amount, 3.0)

    def test_04_show_time_log_action(self):
        """Test show_time_log returns the correct action dictionary."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })
        action = session.show_time_log()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'project.task')
        self.assertEqual(action.get('res_id'), session.task_id.id)
        self.assertEqual(action.get('view_mode'), 'form')

    def test_05_analytic_line_pos_loading_domain(self):
        """Test analytic line load domain restriction based on config & active session."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })

        # 1. Config active - should return domain filtering by active task_id
        domain = self.env['account.analytic.line']._load_pos_data_domain(None, self.pos_config)
        self.assertEqual(domain, [('task_id', '=', session.task_id.id)])

        # 2. Config disabled (time_log = False) - should return empty/fallback domain [('id', '=', 0)]
        config_disabled = self.env['pos.config'].create({
            'name': 'Disabled Config',
            'module_pos_hr': True,
            'time_log': False,
        })
        fallback_domain = self.env['account.analytic.line']._load_pos_data_domain(None, config_disabled)
        self.assertEqual(fallback_domain, [('id', '=', 0)])

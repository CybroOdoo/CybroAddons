# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPosTimesheet(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configure default autopost_bills for res.partner
        cls.env['ir.default'].set(
            'res.partner',
            'autopost_bills',
            'never',
        )

        cls.company = cls.env.user.company_id

        # ---------------------------------------------------------
        # Setup Analytic Plan
        # ---------------------------------------------------------
        cls.analytic_plan = cls.env[
            'account.analytic.plan'
        ].search([], limit=1)

        # ---------------------------------------------------------
        # Setup Analytic Account
        # ---------------------------------------------------------
        cls.analytic_account = cls.env[
            'account.analytic.account'
        ].create({
            'name': 'Test Analytic Account',
            'plan_id': cls.analytic_plan.id,
        })

        # ---------------------------------------------------------
        # Setup Project
        # ---------------------------------------------------------
        cls.project = cls.env['project.project'].create({
            'name': 'POS Timesheet Project',
            'allow_timesheets': True,
            'account_id': cls.analytic_account.id,
        })

        # ---------------------------------------------------------
        # Setup Employee
        # ---------------------------------------------------------
        cls.employee = cls.env['hr.employee'].create({
            'name': 'POS Cashier Employee',
        })

        # ---------------------------------------------------------
        # Setup POS Config
        # ---------------------------------------------------------
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'POS timesheet config',
            'module_pos_hr': True,
            'time_log': True,
            'project_id': cls.project.id,
        })

    def test_01_pos_session_project_validation(self):
        """Test that ValidationError is raised for invalid project settings."""
        # 1. Test missing project
        config_no_project = self.env['pos.config'].create({
            'name': 'No Project Config',
            'module_pos_hr': True,
            'time_log': True,
        })
        with self.assertRaises(
            ValidationError,
            msg="Should raise ValidationError if project is not set on config",
        ):
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
        with self.assertRaises(
            ValidationError,
            msg="Should raise ValidationError if project has timesheets disabled",
        ):
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
        expected_project_name = (
            f"{self.project.display_name}/"
            f"{session.project_sequence_number:05d}"
        )
        self.assertEqual(
            session._get_project_session_name(),
            expected_project_name,
        )

        expected_task_name = (
            f"{self.pos_config.display_name}/"
            f"{session.time_log_sequence_number:05d}"
        )
        self.assertEqual(session._get_time_log_task_name(), expected_task_name)

    def test_03_set_timesheet_creation_and_update(self):
        """Test creating and updating timesheet entries through a session."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })

        # Let's send 120 minutes (2 hours) of check in time
        # timestamp: May 19, 2026 10:00:00 (1779184800000 ms)
        check_in_timestamp = 1779184800000
        check_in_date = datetime.fromtimestamp(check_in_timestamp / 1000).date()

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
            ('date', '=', check_in_date),
        ])
        self.assertEqual(len(timesheet_line), 1)
        self.assertEqual(timesheet_line.unit_amount, 2.0)
        self.assertEqual(timesheet_line.project_id, self.project)
        self.assertEqual(timesheet_line.account_id, self.project.account_id)
        self.assertEqual(
            timesheet_line.name,
            f"{session.name} - {session.task_id.name}",
        )

        # Update the same timesheet line by sending another 60 minutes (1 hour)
        update_data = [{
            'workMinutes': 60,
            'sessionId': session.id,
            'cashierId': self.employee.id,
            'checkInTime': check_in_timestamp,
        }]
        res_update = session.set_timesheet(update_data)
        self.assertTrue(res_update)

        # Verify the existing line is updated to 3.0 hours instead of duplicated.
        updated_timesheet_lines = self.env['account.analytic.line'].search([
            ('task_id', '=', session.task_id.id),
            ('employee_id', '=', self.employee.id),
            ('date', '=', check_in_date),
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
        """Test analytic line loading based on config and active session."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })

        # 1. Config active - should return domain filtering by active task_id
        domain = self.env['account.analytic.line']._load_pos_data_domain({
            'pos.config': self.pos_config,
        })
        self.assertEqual(domain, [('task_id', '=', session.task_id.id)])

        # 2. Disabled config returns the empty fallback domain.
        config_disabled = self.env['pos.config'].create({
            'name': 'Disabled Config',
            'module_pos_hr': True,
            'time_log': False,
        })
        fallback_domain = self.env['account.analytic.line']._load_pos_data_domain({
            'pos.config': config_disabled,
        })
        self.assertEqual(fallback_domain, [('id', '=', 0)])

    def test_06_pos_data_loading_helpers(self):
        """Test POS data helpers expose the timesheet model and fields."""
        session_fields = self.env['pos.session']._load_pos_data_fields(
            self.pos_config,
        )
        self.assertIn('task_id', session_fields)

        models = self.env['pos.session']._load_pos_data_models(self.pos_config)
        self.assertIn('account.analytic.line', models)

        analytic_fields = self.env['account.analytic.line']._load_pos_data_fields(
            self.pos_config,
        )
        self.assertEqual(
            analytic_fields,
            ['employee_id', 'unit_amount', 'task_id'],
        )

        config_disabled = self.env['pos.config'].create({
            'name': 'Disabled Config',
            'module_pos_hr': True,
            'time_log': False,
        })
        disabled_models = self.env['pos.session']._load_pos_data_models(
            config_disabled,
        )
        self.assertNotIn('account.analytic.line', disabled_models)

        # Empty recordsets should not raise.
        self.env['pos.session']._assign_time_log_sequences()
        self.env['pos.session']._ensure_time_log_task()

        # No config, disabled config or config without a session: empty domain.
        self.assertEqual(
            self.env['account.analytic.line']._load_pos_data_domain({}),
            [('id', '=', 0)],
        )
        self.assertEqual(
            self.env['account.analytic.line']._load_pos_data_domain({
                'pos.config': config_disabled,
            }),
            [('id', '=', 0)],
        )
        self.assertEqual(
            self.env['account.analytic.line']._load_pos_data_domain({
                'pos.config': self.pos_config,
            }),
            [('id', '=', 0)],
        )

        # With an active session, only its task's lines are loaded.
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })
        self.assertEqual(
            self.env['account.analytic.line']._load_pos_data_domain({
                'pos.config': self.pos_config,
            }),
            [('task_id', '=', session.task_id.id)],
        )

    def test_07_existing_task_detection(self):
        """Test that an existing task linked to the session is reused."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })
        session.task_id.pos_session_id = False
        session.task_id = False
        existing_task = self.env['project.task'].create({
            'name': 'Existing Session Task',
            'project_id': self.project.id,
            'pos_session_id': session.id,
        })
        session._ensure_time_log_task()
        self.assertEqual(session.task_id, existing_task)

    def test_08_set_timesheet_edge_cases(self):
        """Test set_timesheet ignores invalid sessions, tasks and employees."""
        check_in_timestamp = 1779184800000
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })

        # Unknown session id.
        self.assertTrue(session.set_timesheet([{
            'workMinutes': 30,
            'sessionId': 999999,
            'cashierId': self.employee.id,
            'checkInTime': check_in_timestamp,
        }]))

        # Session without a task.
        config_no_task = self.env['pos.config'].create({
            'name': 'No Task Config',
            'module_pos_hr': True,
            'time_log': True,
            'project_id': self.project.id,
        })
        session_without_task = self.env['pos.session'].create({
            'config_id': config_no_task.id,
        })
        session_without_task.task_id = False
        self.assertTrue(session_without_task.set_timesheet([{
            'workMinutes': 30,
            'sessionId': session_without_task.id,
            'cashierId': self.employee.id,
            'checkInTime': check_in_timestamp,
        }]))

        # Session pointing to a project that does not allow timesheets.
        bad_project = self.env['project.project'].create({
            'name': 'Invalid Timesheet Project',
            'allow_timesheets': False,
        })
        bad_config = self.env['pos.config'].create({
            'name': 'Invalid Project Config',
            'module_pos_hr': True,
            'time_log': True,
            'project_id': self.project.id,
        })
        session_bad_project = self.env['pos.session'].create({
            'config_id': bad_config.id,
        })
        bad_config.project_id = bad_project
        self.assertTrue(session_bad_project.set_timesheet([{
            'workMinutes': 30,
            'sessionId': session_bad_project.id,
            'cashierId': self.employee.id,
            'checkInTime': check_in_timestamp,
        }]))

        # Unknown employee.
        self.assertTrue(session.set_timesheet([{
            'workMinutes': 30,
            'sessionId': session.id,
            'cashierId': 999999,
            'checkInTime': check_in_timestamp,
        }]))

        # Missing timestamp raises a validation error.
        with self.assertRaises(ValidationError):
            session.set_timesheet([{
                'workMinutes': 30,
                'sessionId': session.id,
                'cashierId': self.employee.id,
            }])

    def test_09_set_opening_control(self):
        """Test the session name and task name are updated when opening."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })
        session.set_opening_control(0, "Opening notes")
        self.assertEqual(session.state, 'opened')
        self.assertEqual(session.name, session._get_project_session_name())
        self.assertEqual(session.task_id.name, session._get_time_log_task_name())

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import timedelta
from odoo import fields
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestEmployeeStages(common.TransactionCase):
    """Test suite for Employee Stages module functionality, stage transitions,
    history tracking, duration computation, and user linking wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()

        # Groups for access rights testing
        cls.hr_officer_group = cls.env.ref('hr.group_hr_user')
        cls.hr_manager_group = cls.env.ref('hr.group_hr_manager')

        # Test HR Officer user
        cls.hr_officer = cls.env['res.users'].create({
            'name': 'HR Officer Test',
            'login': 'hr_officer_test',
            'email': 'hr_officer@test.com',
            'group_ids': [(6, 0, [cls.hr_officer_group.id])],
        })

        # Test Employee System User
        cls.test_user = cls.env['res.users'].create({
            'name': 'Employee Test User',
            'login': 'employee_test_user',
            'email': 'employee_user@test.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Primary test employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'John Doe Test',
        })

    def test_01_default_stage_and_history_creation(self):
        """Test default status is 'joined' and initial history line is recorded."""
        self.assertEqual(self.employee.state, 'joined', "Default employee stage must be 'joined'.")
        self.assertEqual(len(self.employee.stages_history_ids), 1, "Initial history entry must be created.")
        history = self.employee.stages_history_ids[0]
        self.assertEqual(history.state, 'joined', "Initial history entry state must be 'joined'.")
        self.assertEqual(history.start_date, self.today, "History start date must be today.")
        self.assertFalse(history.end_date, "Initial ongoing stage should not have an end date.")
        self.assertEqual(history.duration, 0, "Ongoing stage duration must be 0.")

    def test_02_transition_to_grounding(self):
        """Test transition from joined to grounding."""
        self.employee.action_start_grounding()
        self.assertEqual(self.employee.state, 'grounding', "State must transition to 'grounding'.")

        histories = self.employee.stages_history_ids
        self.assertEqual(len(histories), 2, "There should now be 2 stage history entries.")

        joined_history = histories.filtered(lambda h: h.state == 'joined')
        self.assertTrue(joined_history, "Previous joined stage history must exist.")
        self.assertEqual(joined_history.end_date, self.today, "Previous stage end date must be set to today.")

        grounding_history = histories.filtered(lambda h: h.state == 'grounding')
        self.assertTrue(grounding_history, "Grounding stage history must exist.")
        self.assertEqual(grounding_history.start_date, self.today, "Grounding stage start date must be today.")
        self.assertFalse(grounding_history.end_date, "Active grounding stage should not have an end date.")

    def test_03_transition_to_test_period(self):
        """Test transition from grounding to test_period."""
        self.employee.action_start_grounding()
        self.employee.action_start_test_period()
        self.assertEqual(self.employee.state, 'test_period', "State must transition to 'test_period'.")

        histories = self.employee.stages_history_ids
        grounding_history = histories.filtered(lambda h: h.state == 'grounding')
        self.assertEqual(grounding_history.end_date, self.today, "Grounding stage must be closed.")

        test_history = histories.filtered(lambda h: h.state == 'test_period')
        self.assertTrue(test_history, "Test period stage history must exist.")
        self.assertEqual(test_history.start_date, self.today)
        self.assertFalse(test_history.end_date)

    def test_04_set_as_employee_via_wizard_with_user(self):
        """Test transitioning to employment via wizard while linking a user."""
        self.employee.action_start_grounding()
        self.employee.action_start_test_period()

        wizard = self.env['employee.stage'].with_context(active_id=self.employee.id).create({
            'related_user_id': self.test_user.id,
        })
        wizard.set_as_employee()

        self.assertEqual(self.employee.state, 'employment', "State must transition to 'employment'.")
        self.assertEqual(self.employee.user_id, self.test_user, "Employee user_id must be linked.")

        histories = self.employee.stages_history_ids
        test_history = histories.filtered(lambda h: h.state == 'test_period')
        self.assertEqual(test_history.end_date, self.today, "Test period stage must be closed.")

        employment_history = histories.filtered(lambda h: h.state == 'employment')
        self.assertTrue(employment_history, "Employment stage history must exist.")
        self.assertEqual(employment_history.start_date, self.today)
        self.assertFalse(employment_history.end_date)

    def test_05_set_as_employee_direct_from_joined_with_context_employee_id(self):
        """Test promoting directly from joined to employment using employee_id in context."""
        employee2 = self.env['hr.employee'].create({'name': 'Direct Hire'})
        wizard = self.env['employee.stage'].with_context(employee_id=employee2.id).create({})
        wizard.set_as_employee()

        self.assertEqual(employee2.state, 'employment', "Employee must transition directly to 'employment'.")
        histories = employee2.stages_history_ids
        joined_history = histories.filtered(lambda h: h.state == 'joined')
        self.assertEqual(joined_history.end_date, self.today, "Joined stage must be closed.")
        employment_history = histories.filtered(lambda h: h.state == 'employment')
        self.assertTrue(employment_history, "Employment stage must be created.")

    def test_06_transition_to_notice_period(self):
        """Test transition from employment to notice_period."""
        self.employee.set_as_employee()
        self.employee.action_start_notice_period()

        self.assertEqual(self.employee.state, 'notice_period', "State must transition to 'notice_period'.")
        employment_history = self.employee.stages_history_ids.filtered(lambda h: h.state == 'employment')
        self.assertEqual(employment_history.end_date, self.today, "Employment stage must be closed.")

        notice_history = self.employee.stages_history_ids.filtered(lambda h: h.state == 'notice_period')
        self.assertTrue(notice_history, "Notice period history entry must exist.")
        self.assertEqual(notice_history.start_date, self.today)
        self.assertFalse(notice_history.end_date)

    def test_07_transition_to_relieved_and_archive(self):
        """Test relieving an employee sets relieved state, archives record, and creates history."""
        self.employee.set_as_employee()
        self.employee.action_start_notice_period()
        self.employee.action_relived()

        self.assertEqual(self.employee.state, 'relieved', "State must transition to 'relieved'.")
        self.assertFalse(self.employee.active, "Employee must be archived (active=False).")

        relieved_history = self.employee.stages_history_ids.filtered(lambda h: h.state == 'relieved')
        self.assertTrue(relieved_history, "Relieved history entry must exist.")
        self.assertEqual(relieved_history.start_date, self.today)
        self.assertEqual(relieved_history.end_date, self.today)

    def test_08_termination_from_employment_and_grounding(self):
        """Test termination from employment and grounding stages."""
        # 1. Termination from employment
        self.employee.set_as_employee()
        self.employee.action_terminate()

        self.assertEqual(self.employee.state, 'terminate', "State must transition to 'terminate'.")
        self.assertFalse(self.employee.active, "Employee must be archived.")
        term_history = self.employee.stages_history_ids.filtered(lambda h: h.state == 'terminate')
        self.assertTrue(term_history, "Terminate history entry must exist.")
        self.assertEqual(term_history.start_date, self.today)
        self.assertEqual(term_history.end_date, self.today)

        # 2. Termination from grounding
        emp_ground = self.env['hr.employee'].create({'name': 'Trainee Employee'})
        emp_ground.action_start_grounding()
        emp_ground.action_terminate()

        self.assertEqual(emp_ground.state, 'terminate')
        self.assertFalse(emp_ground.active)
        ground_history = emp_ground.stages_history_ids.filtered(lambda h: h.state == 'grounding')
        self.assertEqual(ground_history.end_date, self.today)
        term_history2 = emp_ground.stages_history_ids.filtered(lambda h: h.state == 'terminate')
        self.assertTrue(term_history2)

    def test_09_duration_computation(self):
        """Test calculation of duration in days for various date conditions."""
        past_start = self.today - timedelta(days=15)
        history_record = self.env['hr.employee.status.history'].create({
            'employee_id': self.employee.id,
            'state': 'grounding',
            'start_date': past_start,
            'end_date': self.today,
        })
        self.assertEqual(history_record.duration, 15, "Duration should equal difference in days (15).")

        # Ongoing (end_date is False)
        history_ongoing = self.env['hr.employee.status.history'].create({
            'employee_id': self.employee.id,
            'state': 'test_period',
            'start_date': self.today,
            'end_date': False,
        })
        self.assertEqual(history_ongoing.duration, 0, "Ongoing stage duration must be 0.")

        # Missing start_date
        history_no_start = self.env['hr.employee.status.history'].create({
            'employee_id': self.employee.id,
            'state': 'test_period',
            'start_date': False,
            'end_date': self.today,
        })
        self.assertEqual(history_no_start.duration, 0, "Missing start_date duration must be 0.")

    def test_10_hr_employee_public_stage(self):
        """Test public employee representation reflects the employee state."""
        public_emp = self.env['hr.employee.public'].search([('id', '=', self.employee.id)])
        if public_emp:
            self.assertEqual(public_emp.state, self.employee.state, "Public employee stage must match employee state.")
            self.employee.action_start_grounding()
            self.assertEqual(public_emp.state, 'grounding', "Public employee stage must update accordingly.")

    def test_11_batch_employee_creation(self):
        """Test multi-creation of employees creates status history for all records."""
        vals_list = [
            {'name': 'Multi Employee 1'},
            {'name': 'Multi Employee 2', 'state': 'employment'},
        ]
        employees = self.env['hr.employee'].create(vals_list)
        self.assertEqual(len(employees), 2)
        for emp in employees:
            self.assertEqual(len(emp.stages_history_ids), 1)
            self.assertEqual(emp.stages_history_ids[0].state, emp.state)

    def test_12_access_rights_hr_officer(self):
        """Test access rights for HR Officer on history records and wizard."""
        officer_env = self.env(user=self.hr_officer)
        emp = officer_env['hr.employee'].browse(self.employee.id)

        # HR Officer can read employee and history
        self.assertTrue(emp.stages_history_ids)

        # HR Officer can use the stage wizard
        wizard = officer_env['employee.stage'].with_context(active_id=emp.id).create({})
        wizard.set_as_employee()
        self.assertEqual(emp.state, 'employment')

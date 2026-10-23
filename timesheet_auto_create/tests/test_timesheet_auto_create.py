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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTimesheetAutoCreate(TransactionCase):
    """Test suite for automatic timesheet creation from email reports."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.user = cls.env['res.users'].create({
            'name': 'Test Timesheet Employee User',
            'login': 'test_ts_user@example.com',
            'email': 'test_ts_user@example.com',
            'company_id': cls.company.id,
            'group_ids': [(4, cls.env.ref('hr_timesheet.group_hr_timesheet_user').id)],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Timesheet Employee',
            'work_email': 'test_ts_employee@example.com',
            'user_id': cls.user.id,
            'company_id': cls.company.id,
        })

    def test_01_message_new_with_valid_report_creates_timesheets(self):
        """Test parsing HTML report table to create project, task, and timesheets."""
        html_body = """
        <html>
            <body>
                <p>Hello, here is my daily work report:</p>
                <table border="1">
                    <tr>
                        <th>Sl.No</th>
                        <th>Project</th>
                        <th>Task</th>
                        <th>Status</th>
                        <th>Time (in hr)</th>
                        <th>Remarks</th>
                    </tr>
                    <tr>
                        <td>1</td>
                        <td>Internal ERP Revamp</td>
                        <td>Design Wireframes</td>
                        <td>Ongoing</td>
                        <td>4.5</td>
                        <td>Wireframes completed for accounting</td>
                    </tr>
                    <tr>
                        <td>2</td>
                        <td>Internal ERP Revamp</td>
                        <td>API Integration</td>
                        <td>Completed</td>
                        <td>3.0</td>
                        <td>Completed webhook integration</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        msg_dict = {
            'email_from': 'Test Employee <test_ts_employee@example.com>',
            'subject': 'Daily Work Report - 23 Oct',
            'body': html_body,
        }

        created_line = self.env['account.analytic.line'].message_new(msg_dict)
        self.assertEqual(len(created_line), 1, "message_new must return a single record.")

        # Check created project
        project = self.env['project.project'].search([('name', '=', 'Internal ERP Revamp')], limit=1)
        self.assertTrue(project, "Project 'Internal ERP Revamp' should have been created.")
        self.assertTrue(project.allow_timesheets, "Created project should have allow_timesheets enabled.")

        # Check created tasks
        task_1 = self.env['project.task'].search([
            ('name', '=', 'Design Wireframes'),
            ('project_id', '=', project.id),
        ], limit=1)
        self.assertTrue(task_1, "Task 'Design Wireframes' should have been created.")

        task_2 = self.env['project.task'].search([
            ('name', '=', 'API Integration'),
            ('project_id', '=', project.id),
        ], limit=1)
        self.assertTrue(task_2, "Task 'API Integration' should have been created.")

        # Check created timesheets
        timesheets = self.env['account.analytic.line'].search([
            ('project_id', '=', project.id),
            ('employee_id', '=', self.employee.id),
        ], order='id asc')
        self.assertEqual(len(timesheets), 2, "Two timesheets should be created.")

        self.assertEqual(timesheets[0].task_id, task_1)
        self.assertEqual(timesheets[0].unit_amount, 4.5)
        self.assertEqual(timesheets[0].status, 'ongoing')
        self.assertEqual(timesheets[0].name, 'Wireframes completed for accounting')

        self.assertEqual(timesheets[1].task_id, task_2)
        self.assertEqual(timesheets[1].unit_amount, 3.0)
        self.assertEqual(timesheets[1].status, 'completed')
        self.assertEqual(timesheets[1].name, 'Completed webhook integration')

        # Test mail gateway message_post on returned line works without ensure_one failure
        post_msg = created_line.message_post(body="Test posting comment to thread")
        self.assertTrue(post_msg, "message_post should succeed on returned timesheet.")

    def test_02_message_new_reuses_existing_project_and_task(self):
        """Test that existing project and task are reused instead of duplicated."""
        existing_project = self.env['project.project'].create({
            'name': 'Existing Project Alpha',
            'allow_timesheets': True,
        })
        existing_task = self.env['project.task'].create({
            'name': 'Existing Task Beta',
            'project_id': existing_project.id,
        })

        html_body = """
        <table>
            <tr>
                <th>No</th>
                <th>Project</th>
                <th>Task</th>
                <th>Status</th>
                <th>Time (in hr)</th>
                <th>Remarks</th>
            </tr>
            <tr>
                <td>1</td>
                <td>Existing Project Alpha</td>
                <td>Existing Task Beta</td>
                <td>Completed</td>
                <td>2.0</td>
                <td>Bugfix done</td>
            </tr>
        </table>
        """
        msg_dict = {
            'email_from': 'test_ts_employee@example.com',
            'subject': 'Report for Existing Task',
            'body': html_body,
        }

        created_line = self.env['account.analytic.line'].message_new(msg_dict)
        self.assertEqual(len(created_line), 1)

        project_count = self.env['project.project'].search_count([('name', '=', 'Existing Project Alpha')])
        self.assertEqual(project_count, 1, "Existing project should be reused, not duplicated.")

        task_count = self.env['project.task'].search_count([
            ('name', '=', 'Existing Task Beta'),
            ('project_id', '=', existing_project.id),
        ])
        self.assertEqual(task_count, 1, "Existing task should be reused, not duplicated.")

        self.assertEqual(created_line.project_id, existing_project)
        self.assertEqual(created_line.task_id, existing_task)
        self.assertEqual(created_line.status, 'completed')

    def test_03_message_new_fallback_when_no_employee_matches(self):
        """When no employee matches, return singleton fallback instead of empty recordset."""
        msg_dict = {
            'email_from': 'unknown_person@external-domain.com',
            'subject': 'Daily Report from Non-Employee',
            'body': '<p>Here is my report with no employee</p>',
        }

        fallback_line = self.env['account.analytic.line'].message_new(msg_dict)
        self.assertEqual(len(fallback_line), 1, "Must return a singleton record when no employee matches.")
        self.assertEqual(fallback_line.name, 'Daily Report from Non-Employee')

        # Verify that mail gateway's ensure_one succeeds when posting a message
        msg = fallback_line.message_post(body="Message from mail gateway")
        self.assertTrue(msg)

    def test_04_message_new_fallback_when_no_table_matches(self):
        """When an employee sends an email with no matching table, return singleton fallback with employee."""
        msg_dict = {
            'email_from': 'test_ts_employee@example.com',
            'subject': 'Daily Update without Table',
            'body': '<p>I was working on meetings today, no table attached.</p>',
        }

        fallback_line = self.env['account.analytic.line'].message_new(msg_dict)
        self.assertEqual(len(fallback_line), 1, "Must return a singleton record when no table matches.")
        self.assertEqual(fallback_line.name, 'Daily Update without Table')
        self.assertEqual(fallback_line.employee_id, self.employee, "Employee should be set on fallback line.")

        # Verify ensure_one succeeds on message_post
        msg = fallback_line.message_post(body="Message from mail gateway")
        self.assertTrue(msg)

    def test_05_message_new_with_custom_values(self):
        """Verify custom_values passed to message_new are preserved."""
        html_body = """
        <table>
            <tr><th>No</th><th>Project</th><th>Task</th><th>Status</th><th>Time (in hr)</th><th>Remarks</th></tr>
            <tr><td>1</td><td>Project Gamma</td><td>Task Delta</td><td>Ongoing</td><td>1.5</td><td>Documentation</td></tr>
        </table>
        """
        msg_dict = {
            'email_from': 'test_ts_employee@example.com',
            'subject': 'Report with custom values',
            'body': html_body,
        }
        custom_values = {
            'unit_amount': 2.5,
        }

        created_line = self.env['account.analytic.line'].message_new(msg_dict, custom_values=custom_values)
        self.assertEqual(created_line.unit_amount, 2.5, "custom_values should override unit_amount.")

    def test_06_status_field_definition(self):
        """Verify status field default and values."""
        line = self.env['account.analytic.line'].create({
            'name': 'Test Status Field Line',
            'employee_id': self.employee.id,
        })
        self.assertEqual(line.status, 'ongoing', "Default status must be 'ongoing'.")
        line.status = 'completed'
        self.assertEqual(line.status, 'completed', "Status should update to 'completed'.")

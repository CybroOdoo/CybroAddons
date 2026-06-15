# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
###############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestTimesheetAutoCreate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.user = cls.env["res.users"].create({
            "name": "Timesheet Employee",
            "login": "timesheet.employee@example.com",
            "email": "timesheet.employee@example.com",
            "company_id": cls.company.id,
            "company_ids": [(6, 0, cls.company.ids)],
        })
        cls.employee = cls.env["hr.employee"].create({
            "name": "Timesheet Employee",
            "work_email": "timesheet.employee@example.com",
            "user_id": cls.user.id,
            "company_id": cls.company.id,
        })

    def _build_message(self, rows, email_from=None):
        body_rows = "".join(
            "<tr>{}</tr>".format("".join("<td>{}</td>".format(cell) for cell in row))
            for row in rows
        )
        return {
            "email_from": email_from or self.employee.work_email,
            "body": "<table><tr><td>No</td><td>project_id</td><td>task_id</td>"
            "<td>status</td><td>unit_amount</td><td>name</td></tr>{}</table>".format(
                body_rows
            ),
        }

    def test_message_new_creates_project_task_and_timesheet(self):
        message = self._build_message([
            ["1", "Project Alpha", "Task One", "Completed", "2.5", "Initial report"],
        ])

        result = self.env["account.analytic.line"].message_new(message, {})

        project = self.env["project.project"].search([
            ("name", "=", "Project Alpha"),
        ], limit=1)
        task = self.env["project.task"].search([
            ("name", "=", "Task One"),
            ("project_id", "=", project.id),
        ], limit=1)
        timesheet = self.env["account.analytic.line"].search([
            ("employee_id", "=", self.employee.id),
            ("project_id", "=", project.id),
            ("task_id", "=", task.id),
            ("name", "=", "Initial report"),
        ], limit=1)

        self.assertTrue(project)
        self.assertTrue(task)
        self.assertTrue(timesheet)
        self.assertEqual(timesheet.unit_amount, 2.5)
        self.assertEqual(timesheet.status, "completed")
        self.assertEqual(result, project)

    def test_message_new_reuses_existing_project_and_task(self):
        project = self.env["project.project"].create({"name": "Shared Project"})
        task = self.env["project.task"].create({
            "name": "Shared Task",
            "project_id": project.id,
        })
        message = self._build_message([
            ["1", "Shared Project", "Shared Task", "Ongoing", "1.0", "Follow up"],
        ])

        self.env["account.analytic.line"].message_new(message, {})

        timesheets = self.env["account.analytic.line"].search([
            ("employee_id", "=", self.employee.id),
            ("project_id", "=", project.id),
            ("task_id", "=", task.id),
        ])

        self.assertEqual(len(timesheets), 1)
        self.assertEqual(timesheets.status, "ongoing")

    def test_message_new_returns_task_when_employee_is_missing(self):
        message = self._build_message(
            [["1", "Project Beta", "Task Beta", "Completed", "1.0", "No employee"]],
            email_from="unknown@example.com",
        )

        result = self.env["account.analytic.line"].message_new(message, {})

        task = self.env["project.task"].search([
            ("name", "=", "Task Beta"),
        ], limit=1)

        self.assertEqual(result, task)
        self.assertFalse(self.env["account.analytic.line"].search([
            ("name", "=", "No employee"),
        ]))

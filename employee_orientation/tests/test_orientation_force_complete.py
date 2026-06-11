# -*- coding: utf-8 -*-

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestOrientationForceComplete(TransactionCase):

    def setUp(self):
        super().setUp()
        self.department = self.env["hr.department"].create({
            "name": "Force Complete Department",
        })
        self.employee = self.env["hr.employee"].create({
            "name": "Force Complete Employee",
            "department_id": self.department.id,
        })
        checklist_line = self.env["checklist.line"].create({
            "line_name": "Force Complete Item",
            "responsible_user_id": self.env.user.id,
        })
        checklist = self.env["orientation.checklist"].create({
            "checklist_name": "Force Complete Checklist",
            "checklist_department_id": self.department.id,
            "checklist_line_ids": [Command.set([checklist_line.id])],
        })
        self.orientation = self.env["employee.orientation"].create({
            "employee_id": self.employee.id,
            "date": "2026-06-10 09:00:00",
            "orientation_id": checklist.id,
        })
        self.pending_request = self.env["orientation.request"].create({
            "request_name": "Pending Item",
            "request_orientation_id": self.orientation.id,
            "partner_id": self.env.user.id,
            "employee_id": self.employee.id,
        })
        self.cancelled_request = self.env["orientation.request"].create({
            "request_name": "Cancelled Item",
            "request_orientation_id": self.orientation.id,
            "partner_id": self.env.user.id,
            "employee_id": self.employee.id,
            "state": "cancel",
        })

    def test_compute_pending_lines_keeps_new_requests_only(self):
        wizard = self.env["orientation.force.complete"].create({
            "orientation_id": self.orientation.id,
        })

        wizard._compute_pending_lines()

        self.assertIn(self.pending_request, wizard.orientation_lines_ids)
        self.assertNotIn(self.cancelled_request, wizard.orientation_lines_ids)

    def test_force_complete_completes_pending_lines_and_orientation(self):
        wizard = self.env["orientation.force.complete"].create({
            "orientation_id": self.orientation.id,
        })
        wizard._compute_pending_lines()

        wizard.force_complete()

        self.assertEqual(self.pending_request.state, "complete")
        self.assertEqual(self.cancelled_request.state, "cancel")
        self.assertEqual(self.orientation.state, "complete")

# -*- coding: utf-8 -*-

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEmployeeOrientation(TransactionCase):

    def setUp(self):
        super().setUp()
        self.department = self.env["hr.department"].create({
            "name": "Orientation Department",
        })
        self.employee = self.env["hr.employee"].create({
            "name": "Orientation Employee",
            "department_id": self.department.id,
        })
        self.checklist_line = self.env["checklist.line"].create({
            "line_name": "Prepare Workstation",
            "responsible_user_id": self.env.user.id,
        })
        self.checklist = self.env["orientation.checklist"].create({
            "checklist_name": "New Hire Checklist",
            "checklist_department_id": self.department.id,
            "checklist_line_ids": [Command.set([self.checklist_line.id])],
        })

    def test_create_assigns_orientation_sequence(self):
        orientation = self.env["employee.orientation"].create({
            "employee_id": self.employee.id,
            "date": "2026-06-10 09:00:00",
            "orientation_id": self.checklist.id,
        })

        self.assertNotEqual(orientation.name, "New")
        self.assertTrue(orientation.name.startswith("OR"))
        self.assertEqual(orientation.state, "draft")

    def test_action_confirm_orientation_creates_requests(self):
        orientation = self.env["employee.orientation"].create({
            "employee_id": self.employee.id,
            "date": "2026-06-10 09:00:00",
            "orientation_id": self.checklist.id,
        })

        orientation.action_confirm_orientation()

        self.assertEqual(orientation.state, "confirm")
        self.assertEqual(len(orientation.orientation_request_ids), 1)
        request = orientation.orientation_request_ids
        self.assertEqual(request.request_name, self.checklist_line.line_name)
        self.assertEqual(request.partner_id, self.env.user)
        self.assertEqual(request.employee_id, self.employee)

    def test_action_cancel_orientation_cancels_requests(self):
        orientation = self.env["employee.orientation"].create({
            "employee_id": self.employee.id,
            "date": "2026-06-10 09:00:00",
            "orientation_id": self.checklist.id,
        })
        orientation.action_confirm_orientation()

        orientation.action_cancel_orientation()

        self.assertEqual(orientation.state, "cancel")
        self.assertEqual(orientation.orientation_request_ids.state, "cancel")

    def test_action_complete_orientation_opens_wizard_for_pending_requests(self):
        orientation = self.env["employee.orientation"].create({
            "employee_id": self.employee.id,
            "date": "2026-06-10 09:00:00",
            "orientation_id": self.checklist.id,
        })
        orientation.action_confirm_orientation()

        action = orientation.action_complete_orientation()

        self.assertEqual(action["res_model"], "orientation.force.complete")
        self.assertEqual(action["context"], {"default_orientation_id": orientation.id})
        self.assertEqual(orientation.state, "confirm")

    def test_action_complete_orientation_completes_when_no_pending_requests(self):
        orientation = self.env["employee.orientation"].create({
            "employee_id": self.employee.id,
            "date": "2026-06-10 09:00:00",
            "orientation_id": self.checklist.id,
        })
        orientation.action_confirm_orientation()
        orientation.orientation_request_ids.action_confirm_request()

        orientation.action_complete_orientation()

        self.assertEqual(orientation.state, "complete")

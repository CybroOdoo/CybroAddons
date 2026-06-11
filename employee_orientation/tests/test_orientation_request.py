# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestOrientationRequest(TransactionCase):

    def setUp(self):
        super().setUp()
        self.department = self.env["hr.department"].create({
            "name": "Request Department",
        })
        self.employee = self.env["hr.employee"].create({
            "name": "Request Employee",
            "department_id": self.department.id,
        })
        self.request = self.env["orientation.request"].create({
            "request_name": "Prepare Badge",
            "partner_id": self.env.user.id,
            "employee_id": self.employee.id,
            "request_date": "2026-06-10",
        })

    def test_action_confirm_request_marks_complete(self):
        self.request.action_confirm_request()

        self.assertEqual(self.request.state, "complete")

    def test_action_cancel_request_marks_cancelled(self):
        self.request.action_cancel_request()

        self.assertEqual(self.request.state, "cancel")

    def test_action_confirm_send_mail_returns_compose_action(self):
        action = self.request.action_confirm_send_mail()

        self.assertEqual(action["res_model"], "mail.compose.message")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["context"]["default_model"], "orientation.request")
        self.assertEqual(action["context"]["default_res_ids"], self.request.ids)
        self.assertEqual(
            action["context"]["default_template_id"],
            self.env.ref("employee_orientation.orientation_request_view").id,
        )

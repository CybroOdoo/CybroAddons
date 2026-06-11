# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEmployeeTraining(TransactionCase):

    def setUp(self):
        super().setUp()
        self.department = self.env["hr.department"].create({
            "name": "Training Department",
        })
        self.other_department = self.env["hr.department"].create({
            "name": "Other Training Department",
        })
        self.employee = self.env["hr.employee"].create({
            "name": "Training Employee",
            "department_id": self.department.id,
        })
        self.other_employee = self.env["hr.employee"].create({
            "name": "Other Training Employee",
            "department_id": self.other_department.id,
        })
        self.training = self.env["employee.training"].create({
            "program_name": "Safety Training",
            "program_department_id": self.department.id,
            "program_convener_id": self.env.user.id,
            "date_from": "2026-06-10 09:00:00",
            "date_to": "2026-06-10 11:00:00",
        })

    def test_compute_employee_details_uses_program_department(self):
        self.training._compute_employee_details()

        self.assertIn(self.employee, self.training.training_ids)
        self.assertNotIn(self.other_employee, self.training.training_ids)

    def test_training_state_actions(self):
        self.training.action_confirm_event()
        self.assertEqual(self.training.state, "confirm")

        self.training.action_complete_event()
        self.assertEqual(self.training.state, "complete")

        self.training.action_cancel_event()
        self.assertEqual(self.training.state, "cancel")

    def test_action_confirm_send_mail_returns_compose_action(self):
        action = self.training.action_confirm_send_mail()

        self.assertEqual(action["res_model"], "mail.compose.message")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["context"]["default_model"], "employee.training")
        self.assertEqual(action["context"]["default_res_id"], self.training.id)
        self.assertEqual(
            action["context"]["default_template_id"],
            self.env.ref("employee_orientation.orientation_training_mailer").id,
        )

    def test_print_event_returns_report_action(self):
        action = self.training.print_event()
        report_action = action["context"].get("report_action", action)

        self.assertIn(action["type"], ("ir.actions.report", "ir.actions.act_window"))
        self.assertEqual(
            report_action["report_name"],
            "employee_orientation.print_pack_template",
        )
        self.assertEqual(report_action["data"]["program_name"], self.training.program_name)
        self.assertEqual(report_action["data"]["dept_id"], self.department.id)

# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestResUsers(TransactionCase):

    def test_compute_department_id_uses_linked_employee_department(self):
        department = self.env["hr.department"].create({
            "name": "User Department",
        })
        user = new_test_user(
            self.env,
            login="orientation_user",
            groups="base.group_user",
        )
        self.env["hr.employee"].create({
            "name": "User Employee",
            "department_id": department.id,
            "user_id": user.id,
        })

        user._compute_department_id()

        self.assertEqual(user.department_id, department)

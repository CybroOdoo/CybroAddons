# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEmployeeOrientationReport(TransactionCase):

    def test_get_report_values_returns_department_employees(self):
        department = self.env["hr.department"].create({
            "name": "Report Department",
        })
        other_department = self.env["hr.department"].create({
            "name": "Other Report Department",
        })
        employee = self.env["hr.employee"].create({
            "name": "Report Employee",
            "department_id": department.id,
        })
        self.env["hr.employee"].create({
            "name": "Other Report Employee",
            "department_id": other_department.id,
        })
        data = {
            "dept_id": department.id,
            "program_name": "Orientation Report Program",
            "company_name": self.env.company.name,
            "date_to": "2026-06-10",
            "program_convener": self.env.user.name,
            "duration": 1,
            "hours": 2,
            "minutes": 30,
        }

        values = self.env[
            "report.employee_orientation.print_pack_template"
        ]._get_report_values(employee.ids, data=data)

        self.assertEqual(len(values["data"]), 1)
        self.assertEqual(values["data"][0]["doc_ids"], employee.ids)
        self.assertEqual(values["data"][0]["name"], employee.name)
        self.assertEqual(values["data"][0]["department_id"], department.name)
        self.assertEqual(values["data"][0]["program_name"], data["program_name"])

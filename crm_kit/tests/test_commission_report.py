# -*- coding: utf-8 -*-

import json
from types import SimpleNamespace

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCommissionReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.commission = cls.env["crm.commission"].create({
            "name": "Wizard Commission",
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
            "type": "revenue",
            "revenue_type": "straight",
            "straight_commission_rate": 10.0,
        })
        cls.salesperson = cls.env["res.users"].create({
            "name": "Commission Salesperson",
            "login": "commission_salesperson",
            "commission_id": cls.commission.id,
        })
        cls.team = cls.env["crm.team"].create({
            "name": "Commission Team",
            "member_ids": [(6, 0, cls.salesperson.ids)],
            "commission_id": cls.commission.id,
        })

    def test_onchange_salesperson_ids_sets_visibility_flag(self):
        wizard = self.env["commission.report"].new({
            "salesperson_ids": [(6, 0, self.salesperson.ids)],
        })

        wizard.onchange_salesperson_ids()

        self.assertTrue(wizard.is_sales_person)

    def test_onchange_sales_team_ids_sets_visibility_flag(self):
        wizard = self.env["commission.report"].new({
            "sales_team_ids": [(6, 0, self.team.ids)],
        })

        wizard.onchange_sales_team_ids()

        self.assertTrue(wizard.is_sales_team)

    def test_sales_team_constraint_requires_members(self):
        empty_team = self.env["crm.team"].create({
            "name": "Empty Commission Team",
            "commission_id": self.commission.id,
        })

        with self.assertRaises(ValidationError):
            self.env["commission.report"].create({
                "sales_team_ids": [(6, 0, empty_team.ids)],
            })

    def test_salesperson_constraint_requires_commission(self):
        user = self.env["res.users"].create({
            "name": "No Commission User",
            "login": "no_commission_user",
        })

        with self.assertRaises(ValidationError):
            self.env["commission.report"].create({
                "salesperson_ids": [(6, 0, user.ids)],
            })

    def test_action_print_xls_report_returns_report_action(self):
        wizard = self.env["commission.report"].create({
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
            "salesperson_ids": [(6, 0, self.salesperson.ids)],
        })

        action = wizard.action_print_xls_report()
        options = json.loads(action["data"]["options"])

        self.assertEqual(action["report_type"], "xlsx")
        self.assertEqual(action["data"]["model"], "commission.report")
        self.assertEqual(options["salesperson_ids"], self.salesperson.ids)

    def test_get_xlsx_report_writes_response_stream(self):
        wizard = self.env["commission.report"].create({})
        stream = SimpleNamespace(data=b"")

        def _write(data):
            stream.data += data

        response = SimpleNamespace(stream=SimpleNamespace(write=_write))
        wizard.get_xlsx_report({
            "date": "2026-06-02",
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
            "commission_list": [10.0],
            "total_list": [100.0],
            "commission": [5.0],
            "commission_total": [50.0],
            "commission_name": ["Team Plan"],
            "commission_salesperson": ["Commission Salesperson"],
            "commission_sales_team": ["Commission Team"],
            "user_commission_name": ["Wizard Commission"],
            "user_commission_salesperson": ["Commission Salesperson"],
        }, response)

        self.assertTrue(stream.data.startswith(b"PK"))

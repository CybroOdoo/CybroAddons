# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import datetime
from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLabourSupplyReportWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Wizard Customer"})
        cls.skill = cls.env["skill.details"].create({"name": "Operator"})
        cls.contract = cls.env["labour.supply"].create({
            "customer_id": cls.customer.id,
            "from_date": fields.Date.today(),
            "to_date": fields.Date.today() + datetime.timedelta(days=1),
            "state": "ready",
            "total_amount": 400,
            "skill_ids": [(0, 0, {
                "skill_id": cls.skill.id,
                "from_date": fields.Date.today(),
                "to_date": fields.Date.today() + datetime.timedelta(days=1),
                "number_of_labour_required": 1,
            })],
        })

    def test_action_print_pdf_customer_wise(self):
        wizard = self.env["labour.supply.report"].create({
            "filter": "customer_wise",
            "customer_id": self.customer.id,
            "from_date": fields.Date.today() - datetime.timedelta(days=1),
            "to_date": fields.Date.today() + datetime.timedelta(days=2),
        })
        fake_report = SimpleNamespace(report_action=lambda _docids, data=None: {"kind": "customer", "data": data})

        with patch.object(type(self.env), "ref", autospec=True, return_value=fake_report):
            result = wizard.action_print_pdf()

        self.assertEqual(result["kind"], "customer")
        self.assertEqual(result["data"]["customer_id"], self.customer.name)
        self.assertEqual(result["data"]["datas"][0]["name"], self.customer.name)
        self.assertEqual(result["data"]["datas"][0]["sequence_number"], self.contract.sequence_number)

    def test_action_print_pdf_state_wise(self):
        wizard = self.env["labour.supply.report"].create({
            "filter": "state_wise",
            "state_id": "ready",
            "from_date": fields.Date.today() - datetime.timedelta(days=1),
            "to_date": fields.Date.today() + datetime.timedelta(days=2),
        })
        fake_report = SimpleNamespace(report_action=lambda _docids, data=None: {"kind": "state", "data": data})

        with patch.object(type(self.env), "ref", autospec=True, return_value=fake_report):
            result = wizard.action_print_pdf()

        self.assertEqual(result["kind"], "state")
        self.assertEqual(result["data"]["state_id"], "ready")
        self.assertEqual(result["data"]["datas"][0]["state"], "ready")

    def test_domain_with_only_from_date_and_no_customer(self):
        wizard = self.env["labour.supply.report"].create({
            "filter": "customer_wise",
            "from_date": fields.Date.today() - datetime.timedelta(days=1),
        })
        self.assertEqual(
            wizard._get_report_domain(),
            [("from_date", ">=", wizard.from_date)])
        contracts = self.env["labour.supply"].search(
            wizard._get_report_domain())
        self.assertIn(self.contract, contracts)

    def test_domain_without_to_date_has_no_to_date_condition(self):
        wizard = self.env["labour.supply.report"].create({
            "filter": "state_wise",
            "state_id": "ready",
        })
        self.assertEqual(
            wizard._get_report_domain(), [("state", "=", "ready")])

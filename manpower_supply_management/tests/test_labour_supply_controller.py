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

from odoo.addons.manpower_supply_management.controllers import labour_supply as labour_supply_controller_module


class FakeEnv:
    def __init__(self, env, user):
        self._env = env
        self.user = user
        self.company = env.company

    def __getitem__(self, model):
        return self._env[model]


class FakeRequest:
    def __init__(self, env, user):
        self.env = FakeEnv(env, user)
        self.render_calls = []

    def render(self, template, values=None):
        self.render_calls.append((template, values))
        return {"template": template, "values": values}

    def redirect(self, location):
        return {"redirect": location}


@tagged("post_install", "-at_install")
class TestLabourSupplyController(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = labour_supply_controller_module.LabourSupply()
        cls.customer = cls.env["res.partner"].create({"name": "Website Customer"})
        cls.skill = cls.env["skill.details"].create({"name": "Painter"})
        cls.contract = cls.env["labour.supply"].create({
            "customer_id": cls.customer.id,
            "from_date": fields.Date.today(),
            "to_date": fields.Date.today() + datetime.timedelta(days=1),
            "skill_ids": [(0, 0, {
                "skill_id": cls.skill.id,
                "from_date": fields.Date.today(),
                "to_date": fields.Date.today() + datetime.timedelta(days=1),
                "number_of_labour_required": 1,
            })],
        })

    def test_portal_labour_supplies_renders_current_customer_contracts(self):
        user = SimpleNamespace(partner_id=self.customer)
        fake_request = FakeRequest(self.env, user)

        with patch.object(labour_supply_controller_module, "request", fake_request):
            result = type(self.controller).portal_labour_supplies.__wrapped__(
                self.controller)

        self.assertEqual(result["template"], "manpower_supply_management.portal_labour_supply")
        self.assertIn(self.contract, result["values"]["labour_supplies_portal"])
        self.assertEqual(result["values"]["page_name"], "labour_supplies")

    def test_portal_labour_supply_details_renders_contract(self):
        user = SimpleNamespace(partner_id=self.customer)
        fake_request = FakeRequest(self.env, user)

        with patch.object(labour_supply_controller_module, "request", fake_request):
            result = type(self.controller).portal_labour_supply_details.__wrapped__(
                self.controller, self.contract.id)

        self.assertEqual(result["template"], "manpower_supply_management.portal_labour_supply_details")
        self.assertEqual(result["values"]["contract"], self.contract)
        self.assertEqual(result["values"]["object"], self.contract)
        self.assertEqual(result["values"]["page_name"], "labour_supply")

    def test_portal_labour_supply_details_redirects_when_missing(self):
        user = SimpleNamespace(partner_id=self.customer)
        fake_request = FakeRequest(self.env, user)

        with patch.object(labour_supply_controller_module, "request", fake_request):
            result = type(self.controller).portal_labour_supply_details.__wrapped__(
                self.controller, 0)

        self.assertEqual(result, {"redirect": "/my"})

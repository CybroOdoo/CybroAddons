# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

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

    def test_create_labour_on_supply_renders_current_customer_contracts(self):
        user = SimpleNamespace(
            commercial_partner_id=self.customer.commercial_partner_id,
        )
        fake_request = FakeRequest(self.env, user)

        with patch.object(labour_supply_controller_module, "request", fake_request):
            result = type(self.controller).create_labour_on_supply.__wrapped__(self.controller)

        self.assertEqual(result["template"], "manpower_supply_management.portal_labour_supply")
        self.assertIn(self.contract, result["values"]["labour_supplies_portal"])
        self.assertEqual(result["values"]["page_name"], "labour_supplies_contract")

    def test_labour_on_supply_details_renders_contract_and_lines(self):
        user = SimpleNamespace(
            commercial_partner_id=self.customer.commercial_partner_id,
        )
        fake_request = FakeRequest(self.env, user)

        with patch.object(labour_supply_controller_module, "request", fake_request):
            with patch.object(labour_supply_controller_module.http, "request", fake_request):
                result = type(self.controller).labour_on_supply_details.__wrapped__(
                    self.controller, self.contract.id
                )

        self.assertEqual(result["template"], "manpower_supply_management.portal_labour_supply_details")
        self.assertEqual(result["values"]["labour_contract_rec"], self.contract)
        self.assertEqual(result["values"]["contract"], self.contract)
        self.assertEqual(result["values"]["labour_contract_line_rec"], self.contract.skill_ids)

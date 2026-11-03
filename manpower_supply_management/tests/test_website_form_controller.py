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

from odoo.addons.manpower_supply_management.controllers import manpower_supply_management as website_controller_module


class FakeEnv:
    def __init__(self, env, user):
        self._env = env
        self.user = user
        self.company = env.company

    def __getitem__(self, model):
        return self._env[model]


class FakeForm:
    def __init__(self, data):
        self._data = data

    def getlist(self, key):
        return list(self._data.get(key, []))


class FakeRequest:
    def __init__(self, env, user, form_data=None):
        self.env = FakeEnv(env, user)
        self.httprequest = SimpleNamespace(form=FakeForm(form_data or {}))
        self.render_calls = []

    def render(self, template, values=None):
        self.render_calls.append((template, values))
        return {"template": template, "values": values}


@tagged("post_install", "-at_install")
class TestWebsiteFormController(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = website_controller_module.WebsiteForm()
        cls.skill = cls.env["skill.details"].create({"name": "Mason"})
        cls.customer = cls.env["res.partner"].create({"name": "Portal Customer"})

    def test_labour_supply_renders_for_admin(self):
        admin_user = SimpleNamespace(
            _is_admin=lambda: True,
            partner_id=self.env.user.partner_id,
            commercial_partner_id=self.env.user.partner_id.commercial_partner_id,
        )
        fake_request = FakeRequest(self.env, admin_user)

        with patch.object(website_controller_module, "request", fake_request):
            result = type(self.controller).labour_supply.__wrapped__(self.controller)

        self.assertEqual(result["template"], "manpower_supply_management.labour_supply_single_form")
        self.assertIn(self.skill, result["values"]["skills"])
        self.assertIn(self.customer, result["values"]["customers"])
        self.assertFalse(result["values"]["error"])

    def test_reload_with_error_and_non_admin_customer_scope(self):
        non_admin_user = SimpleNamespace(
            _is_admin=lambda: False,
            partner_id=self.customer,
            commercial_partner_id=self.customer.commercial_partner_id,
        )
        fake_request = FakeRequest(self.env, non_admin_user)

        with patch.object(website_controller_module, "request", fake_request):
            result = self.controller._reload_with_error("bad data")

        self.assertEqual(result["values"]["customers"], self.customer)
        self.assertEqual(result["values"]["error"], "bad data")

    def test_submit_all_returns_validation_error(self):
        user = SimpleNamespace(
            _is_admin=lambda: False,
            partner_id=self.customer,
            commercial_partner_id=self.customer.commercial_partner_id,
        )
        fake_request = FakeRequest(self.env, user)

        with patch.object(website_controller_module, "request", fake_request):
            result = type(self.controller).labour_supply_submit_all.__wrapped__(
                self.controller, customer_id=str(self.customer.id)
            )

        self.assertEqual(result["template"], "manpower_supply_management.labour_supply_single_form")
        self.assertEqual(result["values"]["error"], "Please fill in all required fields.")

    def test_submit_all_creates_contract_and_lines(self):
        user = SimpleNamespace(
            _is_admin=lambda: False,
            partner_id=self.customer,
            commercial_partner_id=self.customer.commercial_partner_id,
        )
        tomorrow = fields.Date.today() + datetime.timedelta(days=1)
        later = tomorrow + datetime.timedelta(days=2)
        fake_request = FakeRequest(
            self.env,
            user,
            form_data={
                "skill_id": [str(self.skill.id)],
                "line_from_date": [str(tomorrow)],
                "line_to_date": [str(later)],
                "line_qty": ["2"],
            },
        )

        with patch.object(website_controller_module, "request", fake_request):
            result = type(self.controller).labour_supply_submit_all.__wrapped__(
                self.controller,
                customer_id=str(self.customer.id),
                req_from_date=str(tomorrow),
                req_to_date=str(later),
            )

        self.assertEqual(result["template"], "manpower_supply_management.tmp_form_success")
        contract = self.env["labour.supply"].search([("customer_id", "=", self.customer.id)], order="id desc", limit=1)
        self.assertEqual(contract.from_date, tomorrow)
        self.assertEqual(contract.to_date, later)
        self.assertEqual(len(contract.skill_ids), 1)
        self.assertEqual(contract.skill_ids.number_of_labour_required, 2)

    def test_submit_all_rejects_customer_not_allowed(self):
        other = self.env["res.partner"].create({"name": "Other Customer"})
        user = SimpleNamespace(
            _is_admin=lambda: False,
            partner_id=self.customer,
            commercial_partner_id=self.customer.commercial_partner_id,
        )
        tomorrow = fields.Date.today() + datetime.timedelta(days=1)
        fake_request = FakeRequest(self.env, user)

        with patch.object(website_controller_module, "request", fake_request):
            result = type(self.controller).labour_supply_submit_all.__wrapped__(
                self.controller,
                customer_id=str(other.id),
                req_from_date=str(tomorrow),
                req_to_date=str(tomorrow),
            )

        self.assertIn("not allowed", result["values"]["error"])
        self.assertFalse(
            self.env["labour.supply"].search([("customer_id", "=", other.id)]))

    def test_submit_all_creates_nothing_when_a_line_is_invalid(self):
        user = SimpleNamespace(
            _is_admin=lambda: False,
            partner_id=self.customer,
            commercial_partner_id=self.customer.commercial_partner_id,
        )
        tomorrow = fields.Date.today() + datetime.timedelta(days=1)
        fake_request = FakeRequest(
            self.env,
            user,
            form_data={
                "skill_id": [str(self.skill.id)],
                "line_from_date": [str(tomorrow)],
                "line_to_date": [str(tomorrow)],
                "line_qty": ["0"],
            },
        )
        count_before = self.env["labour.supply"].search_count(
            [("customer_id", "=", self.customer.id)])

        with patch.object(website_controller_module, "request", fake_request):
            result = type(self.controller).labour_supply_submit_all.__wrapped__(
                self.controller,
                customer_id=str(self.customer.id),
                req_from_date=str(tomorrow),
                req_to_date=str(tomorrow),
            )

        self.assertEqual(
            result["values"]["error"], "Quantity must be at least 1.")
        self.assertEqual(
            self.env["labour.supply"].search_count(
                [("customer_id", "=", self.customer.id)]),
            count_before)

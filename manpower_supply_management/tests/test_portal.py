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

from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.manpower_supply_management.controllers import portal as portal_module


class FakeEnv:
    def __init__(self, env, user):
        self._env = env
        self.user = user
        self.company = env.company

    def __getitem__(self, model):
        return self._env[model]


@tagged("post_install", "-at_install")
class TestPortal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create({"name": "Portal Contact"})
        cls.portal_controller = portal_module.CustomerPortal()

    def test_prepare_portal_counter_values_for_labour_supply_count(self):
        user = SimpleNamespace(partner_id=self.customer)
        fake_request = SimpleNamespace(env=FakeEnv(self.env, user))

        with patch.object(portal_module, "request", fake_request):
            model, domain, access = (
                self.portal_controller._prepare_portal_counter_values(
                    "labour_supply_count"))

        self.assertEqual(model, "labour.supply")
        self.assertEqual(
            domain,
            [("customer_id", "child_of", [self.customer.commercial_partner_id.id])])
        self.assertEqual(access, "read")

    def test_prepare_portal_counter_values_delegates_other_counters(self):
        user = SimpleNamespace(partner_id=self.customer)
        fake_request = SimpleNamespace(env=FakeEnv(self.env, user))

        with patch.object(portal_module, "request", fake_request):
            result = self.portal_controller._prepare_portal_counter_values(
                "unknown_count")

        self.assertEqual(result, (False, False, False))

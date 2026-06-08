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

    def test_prepare_home_portal_values_sets_contact_count(self):
        user = SimpleNamespace(commercial_partner_id=self.customer.commercial_partner_id)
        fake_request = SimpleNamespace(env=FakeEnv(self.env, user))

        self.env["labour.supply"].create({"customer_id": self.customer.id})

        with patch.object(portal_module, "request", fake_request):
            with patch("odoo.addons.portal.controllers.portal.CustomerPortal._prepare_home_portal_values", return_value={"base": True}):
                result = self.portal_controller._prepare_home_portal_values(["contact_count"])

        self.assertEqual(result["contact_count"], 1)
        self.assertTrue(result["base"])

    def test_prepare_home_portal_values_skips_count_when_not_requested(self):
        user = SimpleNamespace(commercial_partner_id=self.customer.commercial_partner_id)
        fake_request = SimpleNamespace(env=FakeEnv(self.env, user))

        with patch.object(portal_module, "request", fake_request):
            with patch("odoo.addons.portal.controllers.portal.CustomerPortal._prepare_home_portal_values", return_value={"base": True}):
                result = self.portal_controller._prepare_home_portal_values([])

        self.assertNotIn("contact_count", result)
        self.assertTrue(result["base"])

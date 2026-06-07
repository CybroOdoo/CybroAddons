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

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from unittest.mock import patch


@tagged('post_install', '-at_install')
class TestWebsiteMenu(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = cls.env.ref('base.group_user')
        group_website_designer = cls.env.ref('website.group_website_designer')
        cls.agent_partner = cls.env['res.partner'].create({
            'name': 'Agent Partner',
            'email': 'agent.partner@example.com',
            'is_agent': True,
        })
        cls.regular_partner = cls.env['res.partner'].create({
            'name': 'Regular Partner',
            'email': 'regular.partner@example.com',
        })
        cls.agent_user = cls.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Shopping Agent User',
            'login': 'shopping.agent.user',
            'email': 'shopping.agent.user@example.com',
            'partner_id': cls.agent_partner.id,
            'group_ids': [Command.set([group_user.id, group_website_designer.id])],
        })
        cls.regular_user = cls.env['res.users'].with_context(
            no_reset_password=True
        ).create({
            'name': 'Shopping Regular User',
            'login': 'shopping.regular.user',
            'email': 'shopping.regular.user@example.com',
            'partner_id': cls.regular_partner.id,
            'group_ids': [Command.set([group_user.id, group_website_designer.id])],
        })

    def test_agent_shop_menu_hidden_for_regular_users(self):
        menu = self.env.ref('shopping_through_agent.agent_shop_menu')

        with patch.object(self.env.registry, 'clear_cache') as clear_cache:
            menu.with_user(self.regular_user)._compute_visible()

        self.assertFalse(menu.with_user(self.regular_user).is_visible)
        self.assertGreaterEqual(clear_cache.call_count, 1)
        self.assertTrue(
            any(call.args == ('templates',) for call in clear_cache.call_args_list)
        )

    def test_agent_shop_menu_visible_for_agents(self):
        menu = self.env.ref('shopping_through_agent.agent_shop_menu')

        menu.with_user(self.agent_user)._compute_visible()

        self.assertTrue(menu.with_user(self.agent_user).is_visible)

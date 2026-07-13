# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command
from odoo.tests.common import TransactionCase


class TestIrUiMenu(TransactionCase):
    """Test menu filtering for restricted users on ir.ui.menu."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.group_user = cls.env.ref('base.group_user')

        cls.action = cls.env['ir.actions.act_window'].create({
            'name': 'Test Action',
            'res_model': 'res.users',
            'view_mode': 'list',
        })
        cls.menu_1 = cls.env['ir.ui.menu'].create({
            'name': 'Test Menu 1',
            'action': f'ir.actions.act_window,{cls.action.id}',
        })
        cls.menu_2 = cls.env['ir.ui.menu'].create({
            'name': 'Test Menu 2',
            'action': f'ir.actions.act_window,{cls.action.id}',
        })

        cls.user = cls.env['res.users'].create({
            'name': 'Restricted User',
            'login': 'restricted_menu_user',
            'group_ids': [Command.set([cls.group_user.id])],
        })
        # Restrict the user from seeing menu_1.
        cls.menu_1.restrict_user_ids = [Command.link(cls.user.id)]

    def test_01_filter_visible_menus_hides_restricted(self):
        """_filter_visible_menus drops menus restricted for the user."""
        self.env.registry.clear_cache()
        menus = (self.menu_1 + self.menu_2).with_user(self.user)
        visible_menus = menus._filter_visible_menus()
        self.assertNotIn(self.menu_1, visible_menus)

    def test_02_system_admin_bypasses_restriction(self):
        """System administrators are never restricted."""
        admin_user = self.env.ref('base.user_admin')
        self.menu_1.restrict_user_ids = [Command.link(admin_user.id)]
        self.env.registry.clear_cache()
        visible_menus = self.menu_1.with_user(admin_user)._filter_visible_menus()
        self.assertIn(self.menu_1, visible_menus)

    def test_03_load_menus_end_to_end(self):
        """End-to-end web-client workflow: the restriction hides the menu in
        ``load_menus`` and reappears (via cache invalidation) once removed."""
        menu_model = self.env['ir.ui.menu']
        # A visible app (root) with a child menu pointing to a readable action.
        app = menu_model.create({'name': 'Hide Menu Test App'})
        child = menu_model.create({
            'name': 'Hide Menu Test Child',
            'parent_id': app.id,
            'action': f'ir.actions.act_window,{self.action.id}',
        })

        user_menus = menu_model.with_user(self.user)

        # Baseline: the child menu is part of the user's loaded menu tree.
        self.env.registry.clear_cache()
        self.assertIn(child.id, user_menus.load_menus(False))

        # Restricting writes to ir.ui.menu, which clears the menu cache.
        child.restrict_user_ids = [Command.link(self.user.id)]
        self.assertNotIn(child.id, user_menus.load_menus(False))

        # Removing the restriction makes the menu reappear.
        child.restrict_user_ids = [Command.unlink(self.user.id)]
        self.assertIn(child.id, user_menus.load_menus(False))

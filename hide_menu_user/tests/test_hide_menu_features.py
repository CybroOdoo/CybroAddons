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


class TestHideMenuFeatures(TransactionCase):
    """Test the Phase 3 features: group restriction, cascade and copy wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.group_user = cls.env.ref('base.group_user')
        cls.menu_model = cls.env['ir.ui.menu']

        # An action so the test menus survive the base visibility filter,
        # which only keeps menus pointing to an accessible action.
        cls.action = cls.env['ir.actions.act_window'].create({
            'name': 'Test Action',
            'res_model': 'res.users',
            'view_mode': 'list',
        })

        # A custom group and a user belonging to it.
        cls.restricted_group = cls.env['res.groups'].create({
            'name': 'Hide Menu Test Group'})
        cls.user = cls.env['res.users'].create({
            'name': 'Group Restricted User',
            'login': 'group_restricted_user',
            'group_ids': [Command.set(
                [cls.group_user.id, cls.restricted_group.id])],
        })

    def test_01_group_restriction_hides_menu(self):
        """Members of a restricted group cannot see the menu."""
        menu = self.menu_model.create({
            'name': 'Group Restricted Menu',
            'action': f'ir.actions.act_window,{self.action.id}',
            'restrict_group_ids': [Command.link(self.restricted_group.id)],
        })
        self.env.registry.clear_cache()
        visible = menu.with_user(self.user)._filter_visible_menus()
        self.assertNotIn(menu, visible)

    def test_02_group_restriction_admin_bypass(self):
        """System administrators bypass group restrictions."""
        admin_user = self.env.ref('base.user_admin')
        menu = self.menu_model.create({
            'name': 'Group Restricted Menu Admin',
            'action': f'ir.actions.act_window,{self.action.id}',
            'restrict_group_ids': [Command.link(self.restricted_group.id)],
        })
        self.env.registry.clear_cache()
        visible = menu.with_user(admin_user)._filter_visible_menus()
        self.assertIn(menu, visible)

    def test_03_action_restrict_submenus(self):
        """Restrictions cascade to all descendant menus."""
        parent = self.menu_model.create({
            'name': 'Parent Menu',
            'restrict_user_ids': [Command.link(self.user.id)],
            'restrict_group_ids': [Command.link(self.restricted_group.id)],
        })
        child = self.menu_model.create({
            'name': 'Child Menu', 'parent_id': parent.id})
        grandchild = self.menu_model.create({
            'name': 'Grandchild Menu', 'parent_id': child.id})

        parent.action_restrict_submenus()

        for menu in (child, grandchild):
            self.assertIn(self.user.id, menu.restrict_user_ids.ids)
            self.assertIn(self.restricted_group.id, menu.restrict_group_ids.ids)

    def test_04_copy_wizard_adds_hidden_menus(self):
        """The copy wizard merges the source user's hidden menus."""
        menu_a = self.menu_model.create({'name': 'Menu A'})
        menu_b = self.menu_model.create({'name': 'Menu B'})

        source = self.env['res.users'].create({
            'name': 'Source User', 'login': 'copy_source_user',
            'group_ids': [Command.set([self.group_user.id])],
            'hide_menu_ids': [Command.set([menu_a.id])],
        })
        target = self.env['res.users'].create({
            'name': 'Target User', 'login': 'copy_target_user',
            'group_ids': [Command.set([self.group_user.id])],
            'hide_menu_ids': [Command.set([menu_b.id])],
        })

        wizard = self.env['hide.menu.copy.wizard'].create({
            'source_user_id': source.id,
            'target_user_ids': [Command.set([target.id])],
        })
        wizard.action_copy()

        # Add-only: the target keeps menu_b and also gets menu_a.
        self.assertIn(menu_a.id, target.hide_menu_ids.ids)
        self.assertIn(menu_b.id, target.hide_menu_ids.ids)
        # The synced restriction is applied on the copied menu too.
        self.assertIn(target.id, menu_a.restrict_user_ids.ids)

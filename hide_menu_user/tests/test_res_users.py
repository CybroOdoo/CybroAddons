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


class TestResUsers(TransactionCase):
    """Test the per-user hidden-menu synchronisation on res.users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.group_user = cls.env.ref('base.group_user')
        cls.group_portal = cls.env.ref('base.group_portal')

        cls.menu_1 = cls.env['ir.ui.menu'].create({'name': 'Test Menu 1'})
        cls.menu_2 = cls.env['ir.ui.menu'].create({'name': 'Test Menu 2'})

        cls.user = cls.env['res.users'].create({
            'name': 'Hide Menu Test User',
            'login': 'hide_menu_test_user',
            'group_ids': [Command.set([cls.group_user.id])],
        })

    def test_01_write_syncs_restrict_user_ids(self):
        """Writing hide_menu_ids mirrors onto the menu restrict_user_ids."""
        self.user.write({'hide_menu_ids': [Command.set([self.menu_1.id])]})
        self.assertIn(self.user.id, self.menu_1.restrict_user_ids.ids)
        self.assertNotIn(self.user.id, self.menu_2.restrict_user_ids.ids)

        # Switching the hidden menu unlinks the old and links the new one.
        self.user.write({'hide_menu_ids': [Command.set([self.menu_2.id])]})
        self.assertNotIn(self.user.id, self.menu_1.restrict_user_ids.ids)
        self.assertIn(self.user.id, self.menu_2.restrict_user_ids.ids)

    def test_02_create_syncs_restrict_user_ids(self):
        """A user created with hide_menu_ids populates restrict_user_ids."""
        user = self.env['res.users'].create({
            'name': 'Created With Hidden Menu',
            'login': 'created_with_hidden_menu',
            'group_ids': [Command.set([self.group_user.id])],
            'hide_menu_ids': [Command.set([self.menu_1.id])],
        })
        self.assertIn(user.id, self.menu_1.restrict_user_ids.ids)

    def test_03_compute_is_show_specific_menu(self):
        """is_show_specific_menu is a pure reflection of internal membership."""
        # Internal user -> page shown (flag False).
        self.assertFalse(self.user.is_show_specific_menu)
        # Non-internal user -> page hidden (flag True).
        portal_user = self.env['res.users'].create({
            'name': 'Portal User',
            'login': 'hide_menu_portal_user',
            'group_ids': [Command.set([self.group_portal.id])],
        })
        self.assertTrue(portal_user.is_show_specific_menu)

    def test_04_downgrade_clears_hidden_menus(self):
        """Losing internal access clears hidden menus and restrictions."""
        self.user.write({'hide_menu_ids': [Command.set([self.menu_1.id])]})
        self.assertIn(self.user.id, self.menu_1.restrict_user_ids.ids)

        # Make the user non-internal.
        self.user.write({
            'group_ids': [Command.set([self.group_portal.id])],
        })
        self.assertFalse(self.user.hide_menu_ids)
        self.assertNotIn(self.user.id, self.menu_1.restrict_user_ids.ids)
        self.assertTrue(self.user.is_show_specific_menu)

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
from odoo.tests.common import TransactionCase
from odoo import Command

class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResUsers, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        cls.menu_1 = cls.env['ir.ui.menu'].create({
            'name': 'Test Menu 1',
        })
        cls.menu_2 = cls.env['ir.ui.menu'].create({
            'name': 'Test Menu 2',
        })
        
        cls.user = cls.env.ref('base.public_user')
        cls.user.write({
            'active': True,
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })

    def test_01_hide_menu_ids_write(self):
        """Test that writing to hide_menu_ids updates restrict_user_ids on the menu."""
        # Add menu_1 to hide_menu_ids
        self.user.write({'hide_menu_ids': [Command.set([self.menu_1.id])]})
        self.assertIn(self.user.id, self.menu_1.restrict_user_ids.ids)
        self.assertNotIn(self.user.id, self.menu_2.restrict_user_ids.ids)
        
        # Change to menu_2
        self.user.write({'hide_menu_ids': [Command.set([self.menu_2.id])]})
        self.assertNotIn(self.user.id, self.menu_1.restrict_user_ids.ids)
        self.assertIn(self.user.id, self.menu_2.restrict_user_ids.ids)

    def test_02_compute_is_show_specific_menu(self):
        """Test compute logic for is_show_specific_menu."""
        # User has base.group_user
        self.assertFalse(self.user.is_show_specific_menu)
        
        # Assign a menu
        self.user.write({'hide_menu_ids': [Command.set([self.menu_1.id])]})
        self.assertIn(self.user.id, self.menu_1.restrict_user_ids.ids)
        
        # Remove base.group_user
        self.user.write({'group_ids': [Command.unlink(self.env.ref('base.group_user').id)]})
        self.assertTrue(self.user.is_show_specific_menu)
        
        # Check that hide_menu_ids is cleared and menu restrictions are removed
        self.assertFalse(self.user.hide_menu_ids)
        self.assertNotIn(self.user.id, self.menu_1.restrict_user_ids.ids)

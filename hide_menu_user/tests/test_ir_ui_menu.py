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

class TestIrUiMenu(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestIrUiMenu, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        cls.action = cls.env['ir.actions.act_window'].create({
            'name': 'Test Action',
            'res_model': 'res.users',
            'view_mode': 'tree',
        })
        cls.menu_1 = cls.env['ir.ui.menu'].create({
            'name': 'Test Menu 1',
            'action': f'ir.actions.act_window,{cls.action.id}'
        })
        cls.menu_2 = cls.env['ir.ui.menu'].create({
            'name': 'Test Menu 2',
            'action': f'ir.actions.act_window,{cls.action.id}'
        })
        
        cls.user_1 = cls.env.ref('base.public_user')
        cls.user_1.write({
            'active': True,
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        
        # Restrict user_1 from seeing menu_1
        cls.menu_1.restrict_user_ids = [Command.link(cls.user_1.id)]

    def test_01_filter_visible_menus(self):
        """Test that _filter_visible_menus hides restricted menus."""
        # Clear the cache for the current user to ensure _filter_visible_menus is run
        self.env.registry.clear_cache()
        
        # User 1 should not see menu 1
        menus = self.env['ir.ui.menu'].with_user(self.user_1).search([('id', 'in', [self.menu_1.id, self.menu_2.id])])
        
        # Call _filter_visible_menus on the recordset
        visible_menus = menus.with_user(self.user_1)._filter_visible_menus()
        
        self.assertNotIn(self.menu_1, visible_menus)
        
        # Note: If menu_2 is not linked to an action, it might be filtered out naturally. 
        # But we only need to test if menu_1 is excluded.

    def test_02_system_admin_bypass(self):
        """Test that system admin bypasses the restriction."""
        admin_user = self.env.ref('base.user_admin')
        # Even if restricted
        self.menu_1.restrict_user_ids = [Command.link(admin_user.id)]
        
        # Clear cache just in case
        self.env.registry.clear_cache()
        
        menus = self.env['ir.ui.menu'].search([('id', '=', self.menu_1.id)])
        visible_menus = menus.with_user(admin_user)._filter_visible_menus()
        
        # Admin should see it, because of group_system role
        self.assertIn(self.menu_1, visible_menus)

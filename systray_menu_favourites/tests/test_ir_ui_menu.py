# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestIrUiMenu(TransactionCase):

    def setUp(self):
        super().setUp()
        self.menu_model = self.env['ir.ui.menu']
        self.act_window_model = self.env['ir.actions.act_window']

    def test_01_search_views_success(self):
        """Test search_views returns correct dictionary details for a valid menu action."""
        action = self.act_window_model.create({
            'name': 'Favourite Partners',
            'res_model': 'res.partner',
            'view_mode': 'kanban,form',
            'target': 'current',
        })

        menu = self.menu_model.create({
            'name': 'Partners Favourites Menu',
            'action': f'ir.actions.act_window,{action.id}',
        })

        res = self.menu_model.search_views(str(menu.id))

        self.assertIsNotNone(res)
        self.assertEqual(res['name'], 'Favourite Partners')
        self.assertEqual(res['model'], 'res.partner')
        self.assertEqual(res['view_mode'], 'kanban,form')
        self.assertEqual(res['target'], 'current')

    def test_02_search_views_non_existent(self):
        """Test search_views returns None for a non-existent menu ID."""
        res = self.menu_model.search_views('999999')
        self.assertIsNone(res)

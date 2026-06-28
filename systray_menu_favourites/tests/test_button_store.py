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
class TestButtonStore(TransactionCase):

    def setUp(self):
        super().setUp()
        self.button_store_model = self.env['button.store']
        self.button_store_model.search([]).unlink()

    def test_01_button_store_crud(self):
        """Test action_create, action_search, and action_remove_view methods of button.store."""
        self.button_store_model.action_create("Contacts Favourite", 101)
        created_records = self.button_store_model.search([('button', '=', 101)])
        self.assertEqual(len(created_records), 1)
        self.assertEqual(created_records.name, "Contacts Favourite")

        search_res = self.button_store_model.action_search()
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0]['name'], "Contacts Favourite")
        self.assertEqual(search_res[0]['button'], 101)

        self.button_store_model.action_remove_view(101)
        remaining_records = self.button_store_model.search([('button', '=', 101)])
        self.assertEqual(len(remaining_records), 0)

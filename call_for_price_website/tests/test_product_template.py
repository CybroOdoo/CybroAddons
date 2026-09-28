# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch

class TestProductTemplate(TransactionCase):
    def setUp(self):
        super(TestProductTemplate, self).setUp()
        self.product_with_call = self.env['product.template'].create({
            'name': 'Product with Call for Price',
            'list_price': 100.0,
            'price_call': True,
        })
        self.product_without_call = self.env['product.template'].create({
            'name': 'Normal Product',
            'list_price': 50.0,
            'price_call': False,
        })

    def test_get_combination_info(self):
        # Mock super() to return a basic dictionary so we don't trigger website context errors
        with patch('odoo.addons.website_sale.models.product_template.ProductTemplate._get_combination_info') as mock_super:
            mock_super.return_value = {'price': 100.0}
            
            combo_info_1 = self.product_with_call._get_combination_info()
            self.assertTrue(combo_info_1.get('price_call'))

            combo_info_2 = self.product_without_call._get_combination_info()
            self.assertFalse(combo_info_2.get('price_call'))

    def test_website_show_quick_add(self):
        with patch('odoo.addons.website_sale.models.product_template.ProductTemplate._website_show_quick_add') as mock_super:
            mock_super.return_value = True
            
            self.assertFalse(self.product_with_call._website_show_quick_add())
            self.assertTrue(self.product_without_call._website_show_quick_add())

    def test_search_render_results_prices(self):
        with patch('odoo.addons.website_sale.models.product_template.ProductTemplate._search_render_results_prices') as mock_super:
            mock_super.return_value = (100.0, 100.0)
            
            combo_info_1 = {'price_call': True}
            price, list_price = self.product_with_call._search_render_results_prices(
                mapping={}, combination_info=combo_info_1
            )
            self.assertEqual(price, 'Not Available For Sale')

            combo_info_2 = {'price_call': False}
            price_2, list_price_2 = self.product_without_call._search_render_results_prices(
                mapping={}, combination_info=combo_info_2
            )
            self.assertEqual(price_2, 100.0)

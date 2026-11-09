# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
# pylint: disable=protected-access
"""Unit test suite for product_price_update_advanced."""
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'product_price_update_advanced')
class TestProductPrice(TransactionCase):
    """Test suite for product.price wizard and price updates."""

    @classmethod
    def setUpClass(cls):
        """Prepare sample product template for testing price updates."""
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Test Price Update Product',
            'list_price': 100.0,
            'standard_price': 50.0,
        })

    def test_action_change_product_price(self):
        """Verify that wizard updates sale and cost price of product."""
        wizard = self.env['product.price'].create({
            'product_id': self.product.id,
            'sale_price': 150.0,
            'cost_price': 75.0,
        })
        action = wizard.action_change_product_price()

        self.assertEqual(self.product.list_price, 150.0)
        self.assertEqual(self.product.standard_price, 75.0)
        self.assertEqual(action.get('res_model'), 'product.template')
        self.assertEqual(action.get('res_id'), self.product.id)
        self.assertEqual(action.get('view_mode'), 'form')

    def test_onchange_product_id(self):
        """Verify that onchange fetches current product prices."""
        wizard = self.env['product.price'].new({
            'product_id': self.product.id,
        })
        wizard._onchange_product_id()

        self.assertEqual(wizard.sale_price, 100.0)
        self.assertEqual(wizard.cost_price, 50.0)

    def test_onchange_product_id_empty(self):
        """Verify that onchange handles empty product gracefully."""
        wizard = self.env['product.price'].new({
            'product_id': False,
        })
        wizard._onchange_product_id()
        self.assertEqual(wizard.sale_price, 0.0)
        self.assertEqual(wizard.cost_price, 0.0)

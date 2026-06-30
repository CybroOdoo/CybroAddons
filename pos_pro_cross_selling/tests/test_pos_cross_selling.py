# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Adarsh K(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestPosCrossSelling(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test products (available in POS)
        cls.main_product = cls.env['product.product'].create({
            'name': 'Main Test Product',
            'available_in_pos': True,
            'lst_price': 100.0,
        })
        cls.cross_product_1 = cls.env['product.product'].create({
            'name': 'Cross Product 1',
            'available_in_pos': True,
            'lst_price': 20.0,
        })
        cls.cross_product_2 = cls.env['product.product'].create({
            'name': 'Cross Product 2',
            'available_in_pos': True,
            'lst_price': 30.0,
        })

    def test_create_cross_selling(self):
        """Test the creation of pos.cross.selling record and its lines."""
        cross_selling = self.env['pos.cross.selling'].create({
            'product_id': self.main_product.id,
            'pos_cross_product_ids': [
                (0, 0, {'product_id': self.cross_product_1.id}),
                (0, 0, {'product_id': self.cross_product_2.id}),
            ]
        })
        self.assertTrue(cross_selling.active)
        self.assertEqual(cross_selling.product_id, self.main_product)
        self.assertEqual(len(cross_selling.pos_cross_product_ids), 2)
        self.assertEqual(cross_selling.pos_cross_product_ids[0].product_id, self.cross_product_1)
        self.assertEqual(cross_selling.pos_cross_product_ids[1].product_id, self.cross_product_2)

    def test_duplicate_product_constraint(self):
        """Test that duplicate pos.cross.selling configuration for the same product is prevented."""
        # Create the first one
        self.env['pos.cross.selling'].create({
            'product_id': self.main_product.id,
        })

        # Try to create a second one for the same main product, which should raise ValidationError
        with self.assertRaises(ValidationError):
            self.env['pos.cross.selling'].create({
                'product_id': self.main_product.id,
            })

    def test_get_cross_selling_products(self):
        """Test get_cross_selling_products method and its returned fields/values."""
        # Setup cross selling
        self.env['pos.cross.selling'].create({
            'product_id': self.main_product.id,
            'pos_cross_product_ids': [
                (0, 0, {'product_id': self.cross_product_1.id}),
                (0, 0, {'product_id': self.cross_product_2.id}),
            ]
        })

        # Call get_cross_selling_products
        result = self.env['pos.cross.selling'].get_cross_selling_products(self.main_product.id)

        self.assertEqual(len(result), 2)

        # Verify the structure and values
        prod1_data = next((p for p in result if p['id'] == self.cross_product_1.id), None)
        self.assertIsNotNone(prod1_data)
        self.assertEqual(prod1_data['name'], 'Cross Product 1')
        self.assertEqual(prod1_data['price'], 20.0)
        self.assertEqual(prod1_data['symbol'], self.cross_product_1.cost_currency_id.symbol)
        self.assertEqual(prod1_data['image'], f'/web/image?model=product.product&field=image_128&id={self.cross_product_1.id}')
        self.assertFalse(prod1_data['selected'])

        prod2_data = next((p for p in result if p['id'] == self.cross_product_2.id), None)
        self.assertIsNotNone(prod2_data)
        self.assertEqual(prod2_data['name'], 'Cross Product 2')
        self.assertEqual(prod2_data['price'], 30.0)
        self.assertEqual(prod2_data['symbol'], self.cross_product_2.cost_currency_id.symbol)
        self.assertEqual(prod2_data['image'], f'/web/image?model=product.product&field=image_128&id={self.cross_product_2.id}')
        self.assertFalse(prod2_data['selected'])

    def test_get_cross_selling_products_empty(self):
        """Test get_cross_selling_products for a product with no cross selling config."""
        result = self.env['pos.cross.selling'].get_cross_selling_products(self.main_product.id)
        self.assertEqual(result, [])

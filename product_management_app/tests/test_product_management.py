# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from datetime import datetime

class TestProductManagement(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env
        
        # Create a product category
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category Management'
        })
        
        # Create products
        cls.product_service = cls.env['product.template'].create({
            'name': 'Service Product test',
            'type': 'service',
            'categ_id': cls.category.id,
        })
        cls.product_consu = cls.env['product.template'].create({
            'name': 'Consumable Product test',
            'type': 'consu',
            'categ_id': cls.category.id,
        })
        
        # Create a partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Management'
        })

        # Create a location
        cls.location = cls.env['stock.location'].create({
            'name': 'Test Location Management',
            'usage': 'internal'
        })

    def test_01_get_data(self):
        """Test getting aggregated product statistics"""
        data = self.env['product.template'].get_data()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('product_templates', data)
        self.assertIn('goods', data)
        self.assertIn('service', data)
        self.assertGreaterEqual(data['product_templates'], 2)
        self.assertGreaterEqual(data['service'], 1)
        self.assertGreaterEqual(data['goods'], 1)

    def test_02_get_top_sale_data(self):
        """Test top sale data retrieval"""
        # Create sale order to have some data
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_consu.product_variant_id.id,
                    'product_uom_qty': 10,
                })
            ]
        })
        sale_order.action_confirm()

        data = self.env['product.template'].get_top_sale_data()
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 2)
        self.assertIn(self.product_consu.name, data[1])

    def test_03_get_top_purchase_data(self):
        """Test top purchase data retrieval"""
        # Create purchase order to have some data
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_consu.product_variant_id.id,
                    'product_qty': 5,
                    'price_unit': 100.0,
                })
            ]
        })
        purchase_order.button_confirm()

        data = self.env['product.template'].get_top_purchase_data()
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 2)
        self.assertIn(self.product_consu.name, data[1])

    def test_04_get_product_location_analysis(self):
        """Test fetching stock locations"""
        data = self.env['product.template'].get_product_location_analysis()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('location_id', data)
        self.assertIn('location_name', data)
        self.assertIn(self.location.id, data['location_id'])

    def test_05_get_products(self):
        """Test fetching all products"""
        data = self.env['product.template'].get_products()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('product_id', data)
        self.assertIn('product_name', data)
        self.assertIn(self.product_consu.id, data['product_id'])
        self.assertIn(self.product_service.id, data['product_id'])

    def test_06_get_years(self):
        """Test fetching last 5 years"""
        years = self.env['product.template'].get_years()
        self.assertTrue(isinstance(years, list))
        self.assertEqual(len(years), 5)
        self.assertEqual(years[0], datetime.now().year)

    def test_07_get_prod_details(self):
        """Test month-wise stock movement for a product"""
        # Create a stock move line
        self.env['stock.move.line'].create({
            'product_id': self.product_consu.product_variant_id.id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.location.id,
            'quantity': 15,
            'company_id': self.env.company.id,
        })
        
        year = str(datetime.now().year)
        data = self.env['product.template'].get_prod_details(self.product_consu.id, year)
        self.assertTrue(isinstance(data, dict))
        self.assertIn('count', data)
        self.assertIn('dates', data)
        self.assertEqual(len(data['count']), 12)
        self.assertEqual(len(data['dates']), 12)

    def test_08_product_move_by_category(self):
        """Test product moves by category"""
        self.env['stock.move.line'].create({
            'product_id': self.product_consu.product_variant_id.id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.location.id,
            'qty_done': 20,
            'company_id': self.env.company.id,
        })
        
        data = self.env['product.template'].product_move_by_category(self.category.id)
        self.assertTrue(isinstance(data, dict))
        self.assertIn('name', data)
        self.assertIn('count', data)

    def test_09_get_product_qty_by_loc(self):
        """Test product quantity by location"""
        self.env['stock.quant'].create({
            'product_id': self.product_consu.product_variant_id.id,
            'location_id': self.location.id,
            'quantity': 50.0,
        })
        
        data = self.env['product.template'].get_product_qty_by_loc(self.location.id)
        self.assertTrue(isinstance(data, dict))
        self.assertIn('products', data)
        self.assertIn('quantity', data)
        if self.product_consu.name in data['products']:
            idx = data['products'].index(self.product_consu.name)
            self.assertEqual(data['quantity'][idx], 50.0)

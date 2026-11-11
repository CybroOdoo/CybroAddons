# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
##############################################################################
from datetime import datetime
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductDashboard(TransactionCase):
    """ Test suite for product.template dashboard reporting and aggregation methods. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Dashboard Partner',
            'email': 'partner@test.com',
        })

        # Product Category
        cls.category = cls.env['product.category'].create({
            'name': 'Test Dashboard Category',
        })

        # Test Products
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Test Dashboard Storable Product',
            'type': 'consu',
            'is_storable': True,
            'categ_id': cls.category.id,
            'list_price': 150.0,
        })
        cls.product = cls.product_tmpl.product_variant_id

        cls.service_tmpl = cls.env['product.template'].create({
            'name': 'Test Dashboard Service Product',
            'type': 'service',
            'categ_id': cls.category.id,
            'list_price': 75.0,
        })

        # Internal Stock Location
        cls.stock_location = cls.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', [cls.company.id, False]),
        ], limit=1)
        if not cls.stock_location:
            cls.stock_location = cls.env['stock.location'].create({
                'name': 'Test Internal Shelf',
                'usage': 'internal',
                'company_id': cls.company.id,
            })

    def test_get_data(self):
        """ Test tile statistics retrieval (get_data). """
        data = self.env['product.template'].get_data()
        expected_keys = {
            'product_templates',
            'product_variants',
            'combo',
            'goods',
            'service',
            'category',
            'price_list',
            'product_attribute',
        }
        self.assertTrue(expected_keys.issubset(data.keys()))
        self.assertGreaterEqual(data['product_templates'], 2)
        self.assertGreaterEqual(data['service'], 1)
        self.assertGreaterEqual(data['category'], 1)

    def test_get_years(self):
        """ Test retrieval of last 5 years. """
        years = self.env['product.template'].get_years()
        current_year = datetime.now().year
        self.assertEqual(len(years), 5)
        self.assertEqual(years[0], current_year)
        self.assertEqual(years[-1], current_year - 4)

    def test_get_products(self):
        """ Test product selection list retrieval. """
        result = self.env['product.template'].get_products()
        self.assertIn('product_id', result)
        self.assertIn('product_name', result)
        self.assertIn(self.product_tmpl.id, result['product_id'])
        self.assertEqual(len(result['product_id']), len(result['product_name']))

    def test_get_top_sale_data(self):
        """ Test top selling products data extraction. """
        # Create a sale order and line
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 15.0,
                    'price_unit': 150.0,
                })
            ]
        })
        sale_data = self.env['product.template'].get_top_sale_data()
        self.assertIsInstance(sale_data, list)
        self.assertEqual(len(sale_data), 2)
        quantities, product_names = sale_data[0], sale_data[1]
        self.assertIsInstance(quantities, list)
        self.assertIsInstance(product_names, list)
        self.assertEqual(len(quantities), len(product_names))
        if quantities:
            self.assertGreaterEqual(quantities[0], 15.0)

    def test_get_top_purchase_data(self):
        """ Test top purchased products data extraction. """
        # Create a purchase order and line
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 25.0,
                    'price_unit': 100.0,
                })
            ]
        })
        purchase_data = self.env['product.template'].get_top_purchase_data()
        self.assertIsInstance(purchase_data, list)
        self.assertEqual(len(purchase_data), 2)
        quantities, product_names = purchase_data[0], purchase_data[1]
        self.assertIsInstance(quantities, list)
        self.assertIsInstance(product_names, list)
        self.assertEqual(len(quantities), len(product_names))
        if quantities:
            self.assertGreaterEqual(quantities[0], 25.0)

    def test_get_product_location_analysis(self):
        """ Test stock location analysis retrieval. """
        loc_data = self.env['product.template'].get_product_location_analysis()
        self.assertIn('location_id', loc_data)
        self.assertIn('location_name', loc_data)
        self.assertEqual(len(loc_data['location_id']), len(loc_data['location_name']))
        self.assertGreater(len(loc_data['location_id']), 0)
        self.assertIn(self.stock_location.id, loc_data['location_id'])

    def test_get_product_qty_by_loc(self):
        """ Test product quantity by location retrieval. """
        # Create stock quant for the product in the location
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.stock_location.id,
            'quantity': 42.0,
        })
        result = self.env['product.template'].get_product_qty_by_loc(self.stock_location.id)
        self.assertIn('products', result)
        self.assertIn('quantity', result)
        self.assertEqual(len(result['products']), len(result['quantity']))
        self.assertIn(42.0, result['quantity'])

    def test_get_prod_details(self):
        """ Test monthly product moves retrieval. """
        current_year = datetime.now().year
        # Normal query
        result = self.env['product.template'].get_prod_details(self.product_tmpl.id, current_year)
        self.assertIn('count', result)
        self.assertIn('dates', result)
        self.assertEqual(len(result['count']), 12)
        self.assertEqual(len(result['dates']), 12)

        # Empty/invalid inputs
        empty_res = self.env['product.template'].get_prod_details(None, None)
        self.assertEqual(len(empty_res['count']), 12)
        self.assertEqual(empty_res['count'], [0] * 12)

    def test_product_move_by_category(self):
        """ Test product moves by category. """
        # Valid category
        result = self.env['product.template'].product_move_by_category(self.category.id)
        self.assertIn('name', result)
        self.assertIn('count', result)

        # Empty category
        empty_result = self.env['product.template'].product_move_by_category(None)
        self.assertEqual(empty_result, {'name': [], 'count': []})

    def test_empty_and_invalid_inputs(self):
        """ Test robustness against non-existent IDs and invalid input types. """
        qty_loc = self.env['product.template'].get_product_qty_by_loc(None)
        self.assertEqual(qty_loc, {'products': [], 'quantity': []})

        qty_invalid = self.env['product.template'].get_product_qty_by_loc('invalid_id')
        self.assertEqual(qty_invalid, {'products': [], 'quantity': []})


# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
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
from unittest.mock import MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.http import _request_stack

class TestProductPerformance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create category
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
        })
        
        # Use standard active company
        cls.company = cls.env.company

        # Create warehouse
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TWH',
            'company_id': cls.company.id,
        })

        # Create products
        cls.product_1 = cls.env['product.template'].create({
            'name': 'Test Product 1',
            'categ_id': cls.category.id,
            'company_id': cls.company.id,
            'type': 'consu',
            'is_storable': True,
        })
        cls.product_2 = cls.env['product.template'].create({
            'name': 'Test Product 2',
            'categ_id': cls.category.id,
            'company_id': cls.company.id,
            'type': 'consu',
            'is_storable': True,
        })

        # Create stock quants
        cls.quant_1 = cls.env['stock.quant'].create({
            'product_id': cls.product_1.product_variant_id.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'quantity': 10.0,
        })
        cls.quant_2 = cls.env['stock.quant'].create({
            'product_id': cls.product_2.product_variant_id.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'quantity': 20.0,
        })

    def setUp(self):
        super().setUp()
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        _request_stack.push(self.mock_request)

    def tearDown(self):
        _request_stack.pop()
        super().tearDown()

    def test_default_category(self):
        wizard = self.env['product.performance'].create({
            'categ_id': self.category.id,
        })
        self.assertTrue(wizard._get_default_category_id())

    def test_date_validation(self):
        # End date before start date should raise UserError
        with self.assertRaises(UserError):
            self.env['product.performance'].create({
                'categ_id': self.category.id,
                'start_date': '2026-06-15',
                'end_date': '2026-06-10',
            })

    def test_product_performance_with_products(self):
        wizard = self.env['product.performance'].create({
            'categ_id': self.category.id,
            'product_ids': [(6, 0, [self.product_1.id])],
            'company_ids': [(6, 0, [self.company.id])],
            'up_to_date_report': True,
        })
        
        action = wizard.product_performance()
        self.assertEqual(action.get('res_model'), 'product.template')
        self.assertIn(self.product_1.id, action.get('domain')[0][2])

    def test_product_performance_without_products(self):
        wizard = self.env['product.performance'].create({
            'categ_id': self.category.id,
            'company_ids': [(6, 0, [self.company.id])],
            'up_to_date_report': True,
        })
        
        action = wizard.product_performance()
        self.assertEqual(action.get('res_model'), 'product.template')
        self.assertIn(self.product_1.id, action.get('domain')[0][2])
        self.assertIn(self.product_2.id, action.get('domain')[0][2])

    def test_product_performance_no_products_error(self):
        # Empty category
        empty_category = self.env['product.category'].create({
            'name': 'Empty Category',
        })
        wizard = self.env['product.performance'].create({
            'categ_id': empty_category.id,
            'company_ids': [(6, 0, [self.company.id])],
        })
        
        with self.assertRaises(UserError):
            wizard.product_performance()


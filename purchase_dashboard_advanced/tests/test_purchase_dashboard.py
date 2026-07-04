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

from odoo.tests import TransactionCase, tagged
from datetime import datetime, timedelta

@tagged('post_install', '-at_install')
class TestPurchaseDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPurchaseDashboard, cls).setUpClass()
        cls.company = cls.env.user.company_id
        
        cls.partner = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.product_category = cls.env['product.category'].create({'name': 'Test Category'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'categ_id': cls.product_category.id,
            'list_price': 100.0,
            'standard_price': 50.0,
        })
        
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'company_id': cls.company.id,
            'priority': '1',
            'order_line': [
                (0, 0, {
                    'name': cls.product.name,
                    'product_id': cls.product.id,
                    'product_qty': 10.0,
                    'price_unit': 50.0,
                })
            ]
        })
        cls.purchase_order.button_confirm()

    def test_01_get_purchase_data(self):
        data = self.env['purchase.order'].get_purchase_data()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('purchase_orders', data)
        self.assertIn('purchase_amount', data)
        self.assertIn('priority_orders', data)
        self.assertIn('vendors', data)

    def test_02_get_yearly_data(self):
        data = self.env['purchase.order'].get_yearly_data()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('purchase_orders', data)
        self.assertIn('purchase_amount', data)
        
    def test_03_get_monthly_data(self):
        data = self.env['purchase.order'].get_monthly_data()
        self.assertTrue(isinstance(data, dict))
        self.assertIn('purchase_orders', data)

    def test_04_get_weekly_data(self):
        data = self.env['purchase.order'].get_weekly_data()
        self.assertTrue(isinstance(data, dict))
        
    def test_05_get_today_data(self):
        data = self.env['purchase.order'].get_today_data()
        self.assertTrue(isinstance(data, dict))

    def test_06_get_select_mode_data(self):
        data = self.env['purchase.order'].get_select_mode_data('today')
        self.assertTrue(isinstance(data, dict))

    def test_07_get_top_chart_data(self):
        data = self.env['purchase.order'].get_top_chart_data('top_product')
        self.assertTrue(isinstance(data, list))
        
        data_vendor = self.env['purchase.order'].get_top_chart_data('top_vendor')
        self.assertTrue(isinstance(data_vendor, list))

        data_rep = self.env['purchase.order'].get_top_chart_data('top_rep')
        self.assertTrue(isinstance(data_rep, list))

    def test_08_get_orders_by_month(self):
        data = self.env['purchase.order'].get_orders_by_month()
        self.assertTrue(isinstance(data, dict))

    def test_09_purchase_vendors(self):
        data = self.env['purchase.order'].purchase_vendors()
        self.assertTrue(isinstance(data, list))

    def test_10_purchase_vendor_details(self):
        data = self.env['purchase.order'].purchase_vendor_details(self.partner.id)
        self.assertTrue(isinstance(data, dict))

    def test_11_get_pending_purchase_data(self):
        data = self.env['purchase.order'].get_pending_purchase_data()
        self.assertTrue(isinstance(data, dict))

    def test_12_get_upcoming_purchase_data(self):
        data = self.env['purchase.order'].get_upcoming_purchase_data()
        self.assertTrue(isinstance(data, dict))

    def test_13_product_categ_analysis(self):
        data = self.env['purchase.order.line'].product_categ_analysis()
        self.assertTrue(isinstance(data, dict))

    def test_14_product_categ_data(self):
        data = self.env['purchase.order.line'].product_categ_data(self.product_category.id)
        self.assertTrue(isinstance(data, dict))

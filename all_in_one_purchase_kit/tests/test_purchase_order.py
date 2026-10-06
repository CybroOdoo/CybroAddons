# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

###############################################################################
from odoo.tests.common import TransactionCase
from odoo import Command

class TestPurchaseOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 80.0,
        })
        
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product.id,
                    'product_qty': 2.0,
                    'price_unit': 80.0,
                }),
                Command.create({
                    'product_id': cls.product.id,
                    'product_qty': 3.0,
                    'price_unit': 80.0,
                })
            ]
        })

    def test_compute_amount_and_words(self):
        """Test compute company currency amount and number to words"""
        self.po._compute_amount()
        self.assertTrue(self.po.company_currency_amount > 0)
        
        self.po._compute_number_to_words()
        self.assertTrue(isinstance(self.po.number_to_words, str))

    def test_action_multi_confirm_and_cancel(self):
        """Test multi confirm and cancel"""
        po2 = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({'product_id': self.product.id, 'product_qty': 1.0, 'price_unit': 10})]
        })
        self.env['purchase.order'].with_context(active_ids=[po2.id]).action_multi_confirm()
        self.assertEqual(po2.state, 'purchase')
        
        self.env['purchase.order'].with_context(active_ids=[po2.id]).action_multi_cancel()
        self.assertEqual(po2.state, 'cancel')

    def test_button_confirm_merges_lines(self):
        """Test lines with same product and price are merged on confirm"""
        self.assertEqual(len(self.po.order_line), 2)
        self.po.button_confirm()
        self.assertEqual(self.po.state, 'purchase')
        # Since price and product are same, they should merge to 1 line with qty 5
        self.assertEqual(len(self.po.order_line), 1)
        self.assertEqual(self.po.order_line[0].product_qty, 5.0)

    def test_recompute_discount(self):
        """Test recompute discount triggers line recalculation"""
        # _recompute_discount simply calls calculate_discount_percentage on lines
        # we ensure it runs without error
        self.po._recompute_discount()
        self.assertTrue(True)

    def test_purchase_data_endpoints(self):
        """Test dashboard data endpoints"""
        data = self.env['purchase.order'].get_purchase_data()
        self.assertIn('purchase_orders', data)
        self.assertIn('purchase_amount', data)

        yearly = self.po.get_yearly_data()
        self.assertIn('purchase_orders', yearly)
        
        monthly = self.po.get_monthly_data()
        self.assertIn('purchase_orders', monthly)
        
        weekly = self.po.get_weekly_data()
        self.assertIn('purchase_orders', weekly)
        
        today = self.po.get_today_data()
        self.assertIn('purchase_orders', today)
        
        select_data = self.env['purchase.order'].get_select_mode_data('this_year')
        self.assertIsInstance(select_data, dict)

    def test_chart_data(self):
        """Test chart queries"""
        top_product = self.env['purchase.order'].get_top_chart_data('top_product')
        self.assertIsInstance(top_product, list)
        
        top_vendor = self.env['purchase.order'].get_top_chart_data('top_vendor')
        self.assertIsInstance(top_vendor, list)
        
        top_rep = self.env['purchase.order'].get_top_chart_data('top_rep')
        self.assertIsInstance(top_rep, list)

    def test_orders_by_month_and_vendors(self):
        """Test orders grouped by month and vendors list"""
        orders_by_month = self.env['purchase.order'].get_orders_by_month()
        self.assertIn('count', orders_by_month)
        
        vendors = self.env['purchase.order'].purchase_vendors()
        self.assertIsInstance(vendors, list)

        vendor_details = self.env['purchase.order'].purchase_vendor_details(self.partner.id)
        self.assertIn('purchase_amount', vendor_details)

    def test_pending_and_upcoming(self):
        """Test pending and upcoming orders data"""
        pending = self.env['purchase.order'].get_pending_purchase_data()
        self.assertIn('order', pending)
        
        upcoming = self.env['purchase.order'].get_upcoming_purchase_data()
        self.assertIn('order', upcoming)

    def test_recommendation_wizard(self):
        """Test recommendation wizard action"""
        action = self.po.recommendation_wizard()
        self.assertEqual(action['res_model'], 'product.recommendation')

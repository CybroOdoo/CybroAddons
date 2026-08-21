# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestLoyaltyCustomerDomain(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100,
        })
        cls.program = cls.env['loyalty.program'].create({
            'name': 'Customer Loyalty Program',
            'applies_on': 'current',
            'program_type': 'loyalty',
            'trigger': 'auto',
        })
        cls.rule = cls.env['loyalty.rule'].create({
            'program_id': cls.program.id,
            'minimum_qty': 1,
            'reward_point_mode': 'order',
            'reward_point_amount': 10,
            'customer_domain': "[('id', '=', %s)]" % cls.customer.id,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.customer.id,
        })
        cls.env['sale.order.line'].create({
            'order_id': cls.sale_order.id,
            'product_id': cls.product.id,
            'product_uom_qty': 1,
            'price_unit': 100,
            'name': 'Test Product',
        })

    def test_customer_domain_field(self):
        """Test customer domain field"""
        self.assertEqual(
            self.rule.customer_domain,
            "[('id', '=', %s)]" % self.customer.id
        )

    def test_loyalty_rule_creation(self):
        """Test loyalty rule creation"""
        self.assertEqual(
            self.rule.program_id,
            self.program
        )
        self.assertEqual(
            self.rule.reward_point_amount,
            10
        )

    def test_customer_matches_domain(self):
        """Test customer domain matching"""
        customers = self.env['res.partner'].search(
            eval(self.rule.customer_domain)
        )
        self.assertIn(
            self.customer,
            customers
        )

    def test_program_check_compute_points(self):
        """Test loyalty points computation"""
        result = self.sale_order._program_check_compute_points(
            self.program
        )
        self.assertTrue(
            result,
            "Program computation result is empty"
        )

    def test_sale_order_creation(self):
        """Test sale order creation"""
        self.assertEqual(
            self.sale_order.partner_id,
            self.customer
        )
        self.assertEqual(
            len(self.sale_order.order_line),
            1
        )

    def test_reward_points_configuration(self):
        """Test reward points configuration"""
        self.assertEqual(
            self.rule.reward_point_mode,
            'order'
        )
        self.assertEqual(
            self.rule.reward_point_amount,
            10
        )
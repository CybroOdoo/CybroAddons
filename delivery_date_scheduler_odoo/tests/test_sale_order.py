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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import timedelta
from odoo import fields
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):
    """Test cases for sale.order model extensions in delivery_date_scheduler_odoo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']

        cls.partner = cls.Partner.create({
            'name': 'Test Delivery Customer',
            'email': 'customer@test.com',
        })

        cls.product = cls.Product.create({
            'name': 'Test Delivery Product',
            'type': 'consu',
            'list_price': 50.0,
        })

    def test_sale_order_user_description_creation(self):
        """Test creating a sale order with custom user_description."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'user_description': 'Please deliver to the front porch.',
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
            })],
        })
        self.assertEqual(
            order.user_description,
            'Please deliver to the front porch.',
            "user_description should be correctly stored during order creation",
        )

    def test_sale_order_user_description_update(self):
        """Test updating user_description on an existing sale order."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
            })],
        })
        self.assertFalse(order.user_description, "user_description should initially be False/empty")

        order.write({'user_description': 'Updated delivery instruction: Leave with neighbor.'})
        self.assertEqual(
            order.user_description,
            'Updated delivery instruction: Leave with neighbor.',
            "user_description should be correctly updated",
        )

    def test_sale_order_copy_user_description(self):
        """Test that user_description is preserved when copying a sale order."""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'user_description': 'Handle with care: Fragile glassware.',
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
            })],
        })
        copied_order = order.copy()
        self.assertEqual(
            copied_order.user_description,
            'Handle with care: Fragile glassware.',
            "user_description should be copied to the new quotation",
        )

    def test_sale_order_confirm_with_commitment_date_and_description(self):
        """Test confirming a quotation with commitment_date and user_description set."""
        delivery_date = fields.Date.today() + timedelta(days=5)
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'commitment_date': delivery_date,
            'user_description': 'Deliver after 4 PM.',
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
            })],
        })
        order.action_quotation_sent()
        self.assertEqual(order.state, 'sent')

        order.action_confirm()
        self.assertEqual(order.state, 'sale', "Order should transition to 'sale' on confirmation")
        self.assertEqual(
            order.commitment_date.date(),
            delivery_date,
            "commitment_date should remain intact after confirmation",
        )
        self.assertEqual(
            order.user_description,
            'Deliver after 4 PM.',
            "user_description should remain intact after confirmation",
        )

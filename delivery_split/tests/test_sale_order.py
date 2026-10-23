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
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):
    """Test cases for sale.order model in delivery_split module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']

        cls.customer_1 = cls.Partner.create({
            'name': 'Primary Customer 1',
            'email': 'customer1@test.com',
        })
        cls.customer_2 = cls.Partner.create({
            'name': 'Primary Customer 2',
            'email': 'customer2@test.com',
        })
        cls.recipient = cls.Partner.create({
            'name': 'Third Party Recipient',
            'email': 'recipient@test.com',
        })

        cls.product_1 = cls.Product.create({
            'name': 'Test Product 1',
            'is_storable': True,
            'list_price': 100.0,
        })
        cls.product_2 = cls.Product.create({
            'name': 'Test Product 2',
            'is_storable': True,
            'list_price': 150.0,
        })

    def test_default_fields(self):
        """Test default values of is_delivery_split and is_consolidate."""
        order = self.SaleOrder.create({
            'partner_id': self.customer_1.id,
        })
        self.assertFalse(order.is_delivery_split, "is_delivery_split should default to False")
        self.assertFalse(order.is_consolidate, "is_consolidate should default to False")

    def test_onchange_partner_id_with_delivery_split(self):
        """Test _onchange_partner_id updates line recipients when is_delivery_split is True."""
        order = self.SaleOrder.create({
            'partner_id': self.customer_1.id,
            'is_delivery_split': True,
            'order_line': [
                Command.create({
                    'product_id': self.product_1.id,
                    'product_uom_qty': 2.0,
                    'recipient_id': self.recipient.id,
                }),
                Command.create({
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1.0,
                    'recipient_id': self.recipient.id,
                }),
            ],
        })

        # Change partner to customer_2 and trigger onchange
        order.partner_id = self.customer_2
        order._onchange_partner_id()

        for line in order.order_line:
            self.assertEqual(
                line.recipient_id,
                self.customer_2,
                "Order line recipient_id should be updated to new customer when is_delivery_split is True",
            )

    def test_onchange_partner_id_without_delivery_split(self):
        """Test _onchange_partner_id does not update line recipients when is_delivery_split is False."""
        order = self.SaleOrder.create({
            'partner_id': self.customer_1.id,
            'is_delivery_split': False,
            'order_line': [
                Command.create({
                    'product_id': self.product_1.id,
                    'product_uom_qty': 2.0,
                    'recipient_id': self.recipient.id,
                }),
            ],
        })

        # Change partner to customer_2 and trigger onchange
        order.partner_id = self.customer_2
        order._onchange_partner_id()

        self.assertEqual(
            order.order_line[0].recipient_id,
            self.recipient,
            "Order line recipient_id should remain unchanged when is_delivery_split is False",
        )

    def test_onchange_partner_id_empty_lines(self):
        """Test _onchange_partner_id executes safely when order has no order lines."""
        order = self.SaleOrder.create({
            'partner_id': self.customer_1.id,
            'is_delivery_split': True,
        })
        order.partner_id = self.customer_2
        try:
            order._onchange_partner_id()
        except Exception as e:
            self.fail(f"_onchange_partner_id raised an exception on empty lines: {e}")

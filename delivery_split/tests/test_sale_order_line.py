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
from odoo.exceptions import AccessError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderLine(TransactionCase):
    """Test cases for sale.order.line model in delivery_split module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']
        cls.SaleOrderLine = cls.env['sale.order.line']

        cls.customer = cls.Partner.create({
            'name': 'Sale Order Customer',
            'email': 'customer@test.com',
        })
        cls.recipient_1 = cls.Partner.create({
            'name': 'Split Recipient 1',
            'email': 'recipient1@test.com',
        })
        cls.recipient_2 = cls.Partner.create({
            'name': 'Split Recipient 2',
            'email': 'recipient2@test.com',
        })

        cls.product = cls.Product.create({
            'name': 'Test Storable Product',
            'is_storable': True,
            'list_price': 50.0,
        })

    def test_recipient_field_assignment(self):
        """Test setting and retrieving recipient_id on sale.order.line."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'recipient_id': self.recipient_1.id,
                }),
            ],
        })
        line = order.order_line[0]
        self.assertEqual(line.recipient_id, self.recipient_1, "Recipient should match the assigned partner.")

    def test_onchange_product_template_id_with_delivery_split(self):
        """Test _onchange_product_template_id populates default recipient when is_delivery_split is True."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
        })
        line = self.SaleOrderLine.new({
            'order_id': order,
            'product_id': self.product,
            'product_template_id': self.product.product_tmpl_id,
        })
        self.assertFalse(line.recipient_id, "Recipient should initially be empty.")

        line._onchange_product_template_id()
        self.assertEqual(
            line.recipient_id.id,
            self.customer.id,
            "Recipient should default to sale order customer when is_delivery_split is True.",
        )

    def test_onchange_product_template_id_preserves_existing_recipient(self):
        """Test _onchange_product_template_id does not overwrite an existing recipient_id."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
        })
        line = self.SaleOrderLine.new({
            'order_id': order,
            'product_id': self.product,
            'product_template_id': self.product.product_tmpl_id,
            'recipient_id': self.recipient_1,
        })

        line._onchange_product_template_id()
        self.assertEqual(
            line.recipient_id,
            self.recipient_1,
            "Existing recipient should not be overwritten by onchange.",
        )

    def test_onchange_product_template_id_without_delivery_split(self):
        """Test _onchange_product_template_id does not set recipient when is_delivery_split is False."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': False,
        })
        line = self.SaleOrderLine.new({
            'order_id': order,
            'product_id': self.product,
            'product_template_id': self.product.product_tmpl_id,
        })

        line._onchange_product_template_id()
        self.assertFalse(
            line.recipient_id,
            "Recipient should remain unset when is_delivery_split is False.",
        )

    def test_prepare_procurement_values_with_recipient(self):
        """Test procurement values include recipient_id as partner_id when delivery_split is True."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'recipient_id': self.recipient_1.id,
                }),
            ],
        })
        line = order.order_line[0]
        values = line._prepare_procurement_values()

        self.assertEqual(
            values.get('partner_id'),
            self.recipient_1.id,
            "Procurement values partner_id should match line recipient_id.",
        )

    def test_prepare_procurement_values_fallback_customer_without_side_effects(self):
        """Test procurement values fallback to order customer when recipient is unset, without side-effect writes."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                }),
            ],
        })
        line = order.order_line[0]
        self.assertFalse(line.recipient_id, "recipient_id should be unset initially.")

        values = line._prepare_procurement_values()
        self.assertEqual(
            values.get('partner_id'),
            self.customer.id,
            "Procurement values partner_id should fallback to order partner_id.",
        )
        self.assertFalse(
            line.recipient_id,
            "_prepare_procurement_values should not write recipient_id to the line as a side effect.",
        )

    def test_prepare_procurement_values_without_delivery_split(self):
        """Test procurement values do not override partner_id with line recipient when delivery_split is False."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': False,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'recipient_id': self.recipient_1.id,
                }),
            ],
        })
        line = order.order_line[0]
        values = line._prepare_procurement_values()

        # When delivery split is False, the procurement partner remains the order shipping address / customer
        self.assertNotEqual(
            values.get('partner_id'),
            self.recipient_1.id,
            "Procurement values partner_id should not use recipient_id when is_delivery_split is False.",
        )

    def test_prepare_procurement_values_ensure_one(self):
        """Test _prepare_procurement_values raises an error when called on a multi-record set."""
        order = self.SaleOrder.create({
            'partner_id': self.customer.id,
            'is_delivery_split': True,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                }),
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 2.0,
                }),
            ],
        })
        with self.assertRaises(ValueError):
            order.order_line._prepare_procurement_values()

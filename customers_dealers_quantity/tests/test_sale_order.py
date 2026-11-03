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
    """Test cases for sale.order onchange_partner_id logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']

        cls.regular_partner = cls.Partner.create({
            'name': 'Regular Customer',
            'dealer': False,
        })
        cls.dealer_partner = cls.Partner.create({
            'name': 'Dealer Customer',
            'dealer': True,
        })

        cls.product = cls.Product.create({
            'name': 'Special Widget',
            'list_price': 100.0,
            'price': 60.0,
            'minimum_quantity': 10.0,
        })

    def test_onchange_partner_id_to_dealer(self):
        """Test changing partner from regular customer to dealer recomputes line prices."""
        order = self.SaleOrder.create({
            'partner_id': self.regular_partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 10.0,
            })],
        })
        self.assertEqual(order.order_line.price_unit, 100.0)

        order.partner_id = self.dealer_partner
        order._onchange_partner_id_dealer_price()
        self.assertEqual(
            order.order_line.price_unit,
            60.0,
            "Price unit on order line should update to dealer price when partner changes to dealer."
        )

    def test_onchange_partner_id_to_non_dealer(self):
        """Test changing partner from dealer to regular customer resets line prices."""
        order = self.SaleOrder.create({
            'partner_id': self.dealer_partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 10.0,
            })],
        })
        self.assertEqual(order.order_line.price_unit, 60.0)

        order.partner_id = self.regular_partner
        order._onchange_partner_id_dealer_price()
        self.assertEqual(
            order.order_line.price_unit,
            100.0,
            "Price unit on order line should revert to standard price when partner changes to non-dealer."
        )

    def test_onchange_partner_id_below_minimum_quantity(self):
        """Test that dealer price is not applied if quantity is below minimum quantity."""
        order = self.SaleOrder.create({
            'partner_id': self.regular_partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 5.0,
            })],
        })
        self.assertEqual(order.order_line.price_unit, 100.0)

        order.partner_id = self.dealer_partner
        order._onchange_partner_id_dealer_price()
        self.assertEqual(
            order.order_line.price_unit,
            100.0,
            "Price unit should remain standard price when ordered quantity is less than minimum quantity."
        )

    def test_onchange_partner_id_empty_lines(self):
        """Test that calling _onchange_partner_id on an order without lines runs without error."""
        order = self.SaleOrder.create({
            'partner_id': self.regular_partner.id,
        })
        order.partner_id = self.dealer_partner
        # Should execute cleanly without error
        order._onchange_partner_id_dealer_price()
        self.assertFalse(order.order_line)

    def test_compatibility_onchange_partner_id(self):
        """Test the _onchange_partner_id compatibility wrapper method."""
        from ..models.sale_order import SaleOrder as CDQSaleOrder
        order = self.SaleOrder.create({
            'partner_id': self.regular_partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 10.0,
            })],
        })
        self.assertEqual(order.order_line.price_unit, 100.0)

        order.partner_id = self.dealer_partner
        CDQSaleOrder._onchange_partner_id(order)
        self.assertEqual(
            order.order_line.price_unit,
            60.0,
            "_onchange_partner_id compatibility wrapper should trigger dealer price update."
        )

    def test_onchange_partner_id_with_section_line(self):
        """Test changing partner on an order with a section line executes cleanly and updates product lines."""
        order = self.SaleOrder.create({
            'partner_id': self.regular_partner.id,
            'order_line': [
                Command.create({
                    'display_type': 'line_section',
                    'name': 'Section Header',
                }),
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 10.0,
                }),
            ],
        })
        order.partner_id = self.dealer_partner
        order._onchange_partner_id_dealer_price()
        product_line = order.order_line.filtered(lambda l: l.product_id)
        self.assertEqual(product_line.price_unit, 60.0)

    def test_onchange_partner_id_product_without_dealer_price(self):
        """Test changing partner to dealer does not affect products without dealer price."""
        regular_prod = self.Product.create({
            'name': 'No Dealer Price Product',
            'list_price': 80.0,
            'price': 0.0,
            'minimum_quantity': 0.0,
        })
        order = self.SaleOrder.create({
            'partner_id': self.regular_partner.id,
            'order_line': [Command.create({
                'product_id': regular_prod.id,
                'product_uom_qty': 15.0,
            })],
        })
        self.assertEqual(order.order_line.price_unit, 80.0)

        order.partner_id = self.dealer_partner
        order._onchange_partner_id_dealer_price()
        self.assertEqual(
            order.order_line.price_unit,
            80.0,
            "Product without dealer pricing should keep standard price."
        )

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
#############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPurchaseOrderLine(TransactionCase):
    """Test suite for purchase order line sequences."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Vendor',
        })
        cls.product_a = cls.env['product.product'].create({
            'name': 'Product A',
            'list_price': 50.0,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Product B',
            'list_price': 100.0,
        })
        cls.product_c = cls.env['product.product'].create({
            'name': 'Product C',
            'list_price': 150.0,
        })

    def test_purchase_order_line_sequence_numbers(self):
        """Test sequential line numbers on standard purchase order lines."""
        order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_qty': 1.0,
                    'price_unit': 50.0,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_qty': 2.0,
                    'price_unit': 100.0,
                }),
                (0, 0, {
                    'product_id': self.product_c.id,
                    'product_qty': 3.0,
                    'price_unit': 150.0,
                }),
            ],
        })

        lines = order.order_line
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0].sequence_number, 1)
        self.assertEqual(lines[1].sequence_number, 2)
        self.assertEqual(lines[2].sequence_number, 3)

    def test_purchase_order_line_with_sections_and_notes(self):
        """Test sequence numbers with sections and notes."""
        order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section Header',
                    'product_qty': 0.0,
                }),
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_qty': 1.0,
                    'price_unit': 50.0,
                }),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'Delivery Note',
                    'product_qty': 0.0,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_qty': 2.0,
                    'price_unit': 100.0,
                }),
            ],
        })

        lines = order.order_line
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0].sequence_number, 1)
        self.assertEqual(lines[1].sequence_number, 1)
        self.assertEqual(lines[2].sequence_number, 2)
        self.assertEqual(lines[3].sequence_number, 2)

    def test_line_without_order(self):
        """Test sequence number for lines not attached to an order."""
        line = self.env['purchase.order.line'].new({
            'product_id': self.product_a.id,
            'product_qty': 1.0,
            'price_unit': 50.0,
        })
        line._compute_sequence_number()
        self.assertEqual(line.sequence_number, 0)

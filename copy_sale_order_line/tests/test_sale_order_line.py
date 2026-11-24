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
class TestSaleOrderLine(TransactionCase):
    """Unit tests for the sale.order.line model in copy_sale_order_line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.order_line = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order.id,
            'product_id': cls.product.id,
            'product_uom_qty': 2.0,
            'price_unit': 100.0,
            'sequence': 10,
        })

    def test_action_copy_line(self):
        """Test duplicating sale order lines via action_copy_line."""
        initial_line_count = len(self.sale_order.order_line)
        self.assertEqual(initial_line_count, 1)
        initial_sequence = self.order_line.sequence

        # Duplicate a single line
        self.order_line.action_copy_line()

        lines = self.sale_order.order_line
        self.assertEqual(len(lines), initial_line_count + 1)

        # Check duplicated line attributes and sequence
        new_line = lines - self.order_line
        self.assertEqual(len(new_line), 1)
        self.assertEqual(new_line.product_id, self.product)
        self.assertEqual(new_line.product_uom_qty, 2.0)
        self.assertEqual(new_line.price_unit, 100.0)
        self.assertEqual(new_line.order_id, self.sale_order)
        self.assertEqual(new_line.sequence, initial_sequence + 1)

        # Test duplicate on multiple lines recordset
        lines_before_multi = self.sale_order.order_line
        count_before_multi = len(lines_before_multi)
        lines_before_multi.action_copy_line()
        self.assertEqual(len(self.sale_order.order_line), count_before_multi * 2)

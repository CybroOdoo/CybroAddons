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
"""Test suite for sale.order custom table reservation fields."""
from datetime import date
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrder(TransactionCase):
    """Test table reservation fields and integration on sale.order."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Diner Customer',
        })
        cls.floor = cls.env['restaurant.floor'].create({
            'name': 'Sale Order Test Floor',
        })
        cls.table = cls.env['restaurant.table'].create({
            'table_number': 12,
            'floor_id': cls.floor.id,
            'rate': 40.0,
        })
        cls.reservation = cls.env['table.reservation'].create({
            'customer_id': cls.partner.id,
            'floor_id': cls.floor.id,
            'booked_tables_ids': [(6, 0, [cls.table.id])],
            'date': date.today(),
            'starting_at': '12:00',
            'ending_at': '14:00',
        })

    def test_sale_order_table_reservation_fields(self):
        """Test persisting and reading table reservation fields on sale.order."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'table_reservation_id': self.reservation.id,
            'tables_ids': [(6, 0, [self.table.id])],
            'floors': self.floor.id,
            'date': date.today(),
            'starting_at': '12:00',
            'ending_at': '14:00',
            'booking_amount': 40.0,
        })

        self.assertEqual(order.table_reservation_id, self.reservation)
        self.assertIn(self.table, order.tables_ids)
        self.assertEqual(order.floors, self.floor.id)
        self.assertEqual(order.date, date.today())
        self.assertEqual(order.starting_at, '12:00')
        self.assertEqual(order.ending_at, '14:00')
        self.assertAlmostEqual(order.booking_amount, 40.0)

    def test_sale_order_line_reservation_pricing(self):
        """Test sale.order.line correctly computes and preserves order-specific booking price."""
        booking_product = self.env.ref(
            'table_reservation_on_website.product_product_table_booking')
        orig_list_price = booking_product.list_price

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'booking_amount': 75.0,
            'order_line': [(0, 0, {
                'product_id': booking_product.id,
                'product_uom_qty': 1,
            })],
        })
        line = order.order_line[0]
        self.assertAlmostEqual(line.price_unit, 75.0)
        # Shared product list_price must not be modified
        self.assertEqual(booking_product.list_price, orig_list_price)


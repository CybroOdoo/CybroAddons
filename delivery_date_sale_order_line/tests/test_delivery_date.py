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
"""Test suite for Sale Delivery by Date module."""
from datetime import timedelta
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDeliveryDateSaleOrderLine(TransactionCase):
    """Unit tests for delivery date on sale order lines and pickings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Delivery Customer',
        })
        cls.product_a = cls.env['product.product'].create({
            'name': 'Delivery Test Product A',
            'is_storable': True,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Delivery Test Product B',
            'is_storable': True,
        })

    def test_sale_order_different_delivery_dates_splits_pickings(self):
        """Test that distinct line delivery dates result in separate pickings."""
        now = fields.Datetime.now()
        date_1 = now + timedelta(days=2)
        date_2 = now + timedelta(days=5)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 3.0,
                    'delivery_datetime': date_1,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom_qty': 5.0,
                    'delivery_datetime': date_2,
                }),
            ],
        })

        order.action_confirm()

        self.assertEqual(len(order.picking_ids), 2, "Separate pickings should be created for different delivery dates")
        picking_dates = {p.delivery_datetime for p in order.picking_ids}
        self.assertIn(date_1, picking_dates)
        self.assertIn(date_2, picking_dates)

        for picking in order.picking_ids:
            self.assertEqual(picking.scheduled_date, picking.delivery_datetime)

    def test_sale_order_same_delivery_date_single_picking(self):
        """Test that lines with the same delivery date are grouped into one picking."""
        delivery_date = fields.Datetime.now() + timedelta(days=3)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 2.0,
                    'delivery_datetime': delivery_date,
                }),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'product_uom_qty': 4.0,
                    'delivery_datetime': delivery_date,
                }),
            ],
        })

        order.action_confirm()

        self.assertEqual(len(order.picking_ids), 1, "Lines with the same delivery date should group into one picking")
        picking = order.picking_ids
        self.assertEqual(picking.delivery_datetime, delivery_date)
        self.assertEqual(picking.scheduled_date, delivery_date)

    def test_sale_order_no_delivery_date_preserves_scheduled_date(self):
        """Test that when no delivery date is provided, scheduled_date is not False."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'delivery_datetime': False,
                }),
            ],
        })

        order.action_confirm()

        self.assertEqual(len(order.picking_ids), 1)
        picking = order.picking_ids
        self.assertFalse(picking.delivery_datetime)
        self.assertTrue(picking.scheduled_date, "Scheduled date must not be wiped out or set to False")

    def test_sale_order_line_past_date_validation(self):
        """Test ValidationError when setting a past delivery date on sale order line."""
        past_date = fields.Datetime.now() - timedelta(days=2)
        with self.assertRaises(ValidationError):
            self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product_a.id,
                        'product_uom_qty': 1.0,
                        'delivery_datetime': past_date,
                    }),
                ],
            })

    def test_stock_move_past_date_allowed_for_backorders(self):
        """Test that stock moves with past delivery date do not raise ValidationError,
        ensuring backorders, move splitting, and late partial deliveries are not blocked.
        """
        past_date = fields.Datetime.now() - timedelta(days=2)
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        move = self.env['stock.move'].create({
            'product_id': self.product_a.id,
            'product_uom_qty': 1.0,
            'location_id': warehouse.lot_stock_id.id,
            'location_dest_id': self.partner.property_stock_customer.id,
            'delivery_datetime': past_date,
        })
        self.assertTrue(move.id)
        self.assertEqual(move.delivery_datetime, past_date)

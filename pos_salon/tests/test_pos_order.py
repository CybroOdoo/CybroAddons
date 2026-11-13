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
from odoo import fields
from odoo.tests import tagged
from .common import TestSalonCommon


@tagged('post_install', '-at_install', 'pos_salon')
class TestPosOrder(TestSalonCommon):
    """Test suite for pos.order salon integration."""

    __test__ = True

    def _create_pos_order(self, booking_ref=False, amount=30.0):
        """Helper to create a test POS session and order."""
        session = self.env['pos.session'].search([
            ('config_id', '=', self.pos_config.id),
            ('state', 'in', ['opened', 'draft']),
        ], limit=1)
        if not session:
            session = self.env['pos.session'].create({
                'config_id': self.pos_config.id,
                'user_id': self.env.user.id,
            })

        order_vals = {
            'session_id': session.id,
            'salon_booking_ref': booking_ref or 0,
            'partner_id': self.customer_partner.id,
            'lines': [(0, 0, {
                'product_id': self.amenity_spa.id,
                'price_unit': amount,
                'qty': 1.0,
                'price_subtotal': amount,
                'price_subtotal_incl': amount,
            })],
            'amount_total': amount,
            'amount_tax': 0.0,
            'amount_paid': amount,
            'amount_return': 0.0,
        }
        order = self.env['pos.order'].create(order_vals)

        # If payment methods exist, record payment
        if self.pos_config.payment_method_ids:
            self.env['pos.payment'].create({
                'pos_order_id': order.id,
                'amount': amount,
                'payment_date': fields.Datetime.now(),
                'payment_method_id': self.pos_config.payment_method_ids[0].id,
            })

        return order

    def test_01_action_pos_order_paid_marks_booking_paid(self):
        """When POS order with salon_booking_ref is paid, linked salon.booking must be marked as paid."""
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'confirmed',
            'payment_state': 'unpaid',
            'amount_total': 30.0,
            'config_id': self.pos_config.id,
        })
        self.assertEqual(booking.payment_state, 'unpaid')
        self.assertFalse(booking.pos_order_id)

        order = self._create_pos_order(booking_ref=booking.id, amount=30.0)
        order.action_pos_order_paid()

        self.assertEqual(booking.payment_state, 'paid')
        self.assertEqual(booking.pos_order_id, order)

    def test_02_action_pos_order_paid_without_booking_ref(self):
        """A normal POS order without salon_booking_ref processes without modifying salon bookings."""
        order = self._create_pos_order(booking_ref=False, amount=30.0)
        order.action_pos_order_paid()
        self.assertEqual(order.state, 'paid')

    def test_03_action_pos_order_paid_invalid_booking_ref(self):
        """An order pointing to a non-existent booking ref processes cleanly without error."""
        non_existent_id = 99999999
        order = self._create_pos_order(booking_ref=non_existent_id, amount=30.0)
        order.action_pos_order_paid()
        self.assertEqual(order.state, 'paid')

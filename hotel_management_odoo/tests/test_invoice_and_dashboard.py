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
from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import HotelCommon


@tagged('post_install', '-at_install')
class TestInvoiceAndDashboard(HotelCommon):

    def test_action_invoice_creates_move(self):
        food = self._make_food(price=5.0)
        booking = self._make_booking(
            days=2,
            food_order_line_ids=[Command.create({'food_id': food.id, 'uom_qty': 3})])
        res = booking.action_invoice()
        self.assertEqual(res['res_model'], 'account.move')
        move = self.env['account.move'].browse(res['res_id'])
        self.assertEqual(move.ref, booking.name)
        self.assertEqual(move.partner_id, self.partner)
        self.assertEqual(set(move.invoice_line_ids.mapped('product_type')), {'room', 'food'})
        self.assertEqual(booking.invoice_status, 'invoiced')
        self.assertTrue(booking.invoice_button_visible)

    def test_action_done_blocked_by_unpaid_invoice(self):
        booking = self._make_booking()
        self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.partner.id,
            'ref': booking.name})
        with self.assertRaises(ValidationError):
            booking.action_done()
        self.assertNotEqual(booking.state, 'done')

    def test_get_details_events_vehicles_food_checkout(self):
        now = fields.Datetime.now()
        self.env['event.event'].create({
            'name': 'Today', 'date_begin': now - timedelta(hours=1),
            'date_end': now + timedelta(minutes=30)})
        vehicle = self._make_vehicle()
        self._make_food()
        food = self._make_food('Burger')
        booking = self._make_booking(
            vehicle_line_ids=[Command.create({'fleet_id': vehicle.id})],
            food_order_line_ids=[Command.create({'food_id': food.id})])
        booking.room_line_ids.checkout_date = now
        details = self.env['room.booking'].get_details()
        self.assertGreaterEqual(details['total_event'], 1)
        self.assertGreaterEqual(details['pending_events'], 1)
        self.assertGreaterEqual(details['total_vehicle'], 1)
        self.assertGreaterEqual(details['food_items'], 2)
        self.assertGreaterEqual(details['food_order'], 1)
        self.assertGreaterEqual(details['check_out'], 1)
        self.assertGreaterEqual(details['staff'], 1)

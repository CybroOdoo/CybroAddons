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
class TestRoomBooking(HotelCommon):

    def test_amount_totals_all_categories(self):
        vehicle = self._make_vehicle(price=2.0)
        food = self._make_food(price=8.0)
        event = self.env['event.event'].create({
            'name': 'Gala',
            'date_begin': fields.Datetime.now(),
            'date_end': fields.Datetime.now() + timedelta(days=1)})
        booking = self._make_booking(
            days=2,
            need_service=True, need_fleet=True, need_food=True, need_event=True,
            service_line_ids=[Command.create({'service_id': self.service.id, 'uom_qty': 3})],
            vehicle_line_ids=[Command.create({'fleet_id': vehicle.id, 'uom_qty': 10})],
            food_order_line_ids=[Command.create({'food_id': food.id, 'uom_qty': 2})],
            event_line_ids=[Command.create({'event_id': event.id, 'uom_qty': 1})],
        )
        self.assertAlmostEqual(booking.amount_untaxed_room, 200.0)
        self.assertAlmostEqual(booking.amount_untaxed_service, 30.0)
        self.assertAlmostEqual(booking.amount_untaxed_fleet, 20.0)
        self.assertAlmostEqual(booking.amount_untaxed_food, 16.0)
        self.assertAlmostEqual(booking.amount_untaxed, 266.0 + booking.amount_untaxed_event)
        self.assertAlmostEqual(
            booking.amount_total, booking.amount_untaxed + booking.amount_tax)
        self.assertAlmostEqual(booking.amount_total_room, 200.0)

    def test_duplicate_room_constraint(self):
        booking = self._make_booking()
        now = fields.Datetime.now()
        with self.assertRaises(ValidationError):
            booking.write({'room_line_ids': [Command.create({
                'room_id': self.room1.id, 'checkin_date': now,
                'checkout_date': now + timedelta(days=1), 'uom_qty': 1})]})

    def test_reserve_checkin_checkout_done_flow(self):
        booking = self._make_booking(rooms=self.room1 | self.room2)
        res = booking.action_reserve()
        self.assertEqual(res['params']['type'], 'success')
        self.assertEqual(booking.state, 'reserved')
        self.assertEqual(self.room1.status, 'reserved')
        self.assertFalse(self.room1.is_room_avail)
        # reserving again returns a warning
        res = booking.action_reserve()
        self.assertEqual(res['params']['type'], 'warning')
        res = booking.action_checkin()
        self.assertEqual(res['params']['type'], 'success')
        self.assertEqual(booking.state, 'check_in')
        self.assertEqual(self.room2.status, 'occupied')
        booking.action_checkout()
        self.assertEqual(booking.state, 'check_out')
        self.assertEqual(self.room1.status, 'available')
        self.assertTrue(self.room1.is_room_avail)
        # cannot be set as done without an invoice ...
        with self.assertRaises(ValidationError):
            booking.action_done()
        self.assertEqual(booking.state, 'check_out')
        # ... nor with an invoice that is not (fully) paid
        move = self.env['account.move'].browse(
            booking.action_invoice()['res_id'])
        with self.assertRaises(ValidationError):
            booking.action_done()
        move.payment_state = 'partial'
        with self.assertRaises(ValidationError):
            booking.action_done()
        self.assertEqual(booking.state, 'check_out')
        # fully paid: the booking can be set as done
        move.payment_state = 'paid'
        res = booking.action_done()
        self.assertEqual(booking.state, 'done')
        self.assertFalse(booking.is_checkin)
        self.assertEqual(res['params']['type'], 'success')

    def test_done_blocked_by_items_added_after_invoice(self):
        booking = self._make_booking()
        move = self.env['account.move'].browse(
            booking.action_invoice()['res_id'])
        move.payment_state = 'paid'
        food = self._make_food(price=5.0)
        booking.write({'food_order_line_ids': [Command.create(
            {'food_id': food.id, 'uom_qty': 1})]})
        with self.assertRaises(ValidationError):
            booking.action_done()

    def test_actions_without_rooms_raise(self):
        booking = self.env['room.booking'].create({'partner_id': self.partner.id})
        for method in ('action_reserve', 'action_checkin',
                       'action_maintenance_request', 'action_invoice'):
            with self.assertRaises(ValidationError, msg=method):
                getattr(booking, method)()

    def test_cancel_frees_rooms(self):
        booking = self._make_booking()
        booking.action_reserve()
        booking.action_cancel()
        self.assertEqual(booking.state, 'cancel')
        self.assertEqual(self.room1.status, 'available')
        self.assertTrue(self.room1.is_room_avail)
        # cancel without lines
        empty = self.env['room.booking'].create({'partner_id': self.partner.id})
        empty.action_cancel()
        self.assertEqual(empty.state, 'cancel')

    def test_action_maintenance_request(self):
        booking = self._make_booking()
        res = booking.action_maintenance_request()
        self.assertEqual(res['params']['type'], 'success')
        self.assertTrue(booking.maintenance_request_sent)
        request = self.env['maintenance.request'].search([
            ('name', '=', 'Maintenance Request - %s' % booking.name)])
        self.assertEqual(len(request), 1)
        self.assertEqual(request.type, 'room')
        self.assertTrue(request.is_hotel)
        self.assertEqual(request.room_maintenance_ids, self.room1)

    def test_view_and_wizard_actions(self):
        booking = self._make_booking()
        act = booking.action_view_invoices()
        self.assertEqual(act['res_model'], 'account.move')
        self.assertEqual(act['domain'], [('ref', '=', booking.name)])
        act = booking.action_compute_bill()
        self.assertEqual(act['res_model'], 'compute.bill')
        self.assertEqual(act['context']['default_booking_id'], booking.id)

    def test_has_pos_orders_and_invoice_count(self):
        booking = self._make_booking()
        self.assertFalse(booking.has_pos_orders)
        self.assertEqual(booking.invoice_count, 0)
        self.env['account.move'].create({
            'move_type': 'out_invoice', 'partner_id': self.partner.id,
            'ref': booking.name})
        booking.invalidate_recordset()
        self.assertEqual(booking.invoice_count, 1)

    def test_bill_summary_lines(self):
        booking = self._make_booking()
        lines = booking.get_bill_summary_lines()
        self.assertEqual(lines[0]['reference'], booking.name)
        self.assertEqual(len(lines), 1)

    def test_create_list(self):
        food = self._make_food(price=5.0)
        vehicle = self._make_vehicle(price=3.0)
        event = self.env['event.event'].create({
            'name': 'Show', 'date_begin': fields.Datetime.now(),
            'date_end': fields.Datetime.now() + timedelta(days=1)})
        booking = self._make_booking(
            food_order_line_ids=[Command.create({'food_id': food.id, 'uom_qty': 2})],
            vehicle_line_ids=[Command.create({'fleet_id': vehicle.id, 'uom_qty': 4})],
            service_line_ids=[Command.create({'service_id': self.service.id})],
            event_line_ids=[Command.create({'event_id': event.id})])
        res = booking.create_list(booking.food_order_line_ids)
        self.assertEqual(res, {'name': 'Pizza', 'quantity': 2, 'price_unit': 5.0,
                               'product_type': 'food'})
        res = booking.create_list(booking.vehicle_line_ids)
        self.assertEqual(res['product_type'], 'fleet')
        res = booking.create_list(booking.service_line_ids)
        self.assertEqual(res['product_type'], 'service')
        res = booking.create_list(booking.event_line_ids)
        self.assertEqual(res['product_type'], 'event')

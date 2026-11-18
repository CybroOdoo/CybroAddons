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
import io
import json
from datetime import date

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import HotelCommon


class _FakeStream:
    def __init__(self):
        self.buffer = io.BytesIO()

    def write(self, data):
        self.buffer.write(data)


class _FakeResponse:
    def __init__(self):
        self.stream = _FakeStream()


@tagged('post_install', '-at_install')
class TestWizards(HotelCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.booking = cls._make_booking(days=2)

    # ---- room.booking.detail ----
    def test_room_detail_generate_data(self):
        wiz = self.env['room.booking.detail'].create({})
        data = wiz.generate_data()
        self.assertTrue(any(d['name'] == self.booking.name for d in data))
        rec = [d for d in data if d['name'] == self.booking.name][0]
        self.assertEqual(rec['room'], 'Room 101')
        self.assertEqual(rec['partner_id'], 'Test Guest')

    def test_room_detail_invalid_dates(self):
        wiz = self.env['room.booking.detail'].create({
            'checkin': date(2026, 5, 10), 'checkout': date(2026, 5, 1)})
        with self.assertRaises(ValidationError):
            wiz.generate_data()

    def test_room_detail_xlsx(self):
        wiz = self.env['room.booking.detail'].create({})
        response = _FakeResponse()
        wiz.get_xlsx_report({'booking': wiz.generate_data()}, response)
        content = response.stream.buffer.getvalue()
        self.assertTrue(content.startswith(b'PK'))

    # ---- sale.order.detail ----

    def test_sale_detail_generate_data(self):
        wiz = self.env['sale.order.detail'].create({})
        data = wiz.generate_data()
        rec = [d for d in data if d['name'] == self.booking.name]
        self.assertEqual(len(rec), 1)
        self.assertEqual(rec[0]['partner_id'], 'Test Guest')

    def test_sale_detail_xlsx_and_report_model(self):
        wiz = self.env['sale.order.detail'].create({})
        data = {'booking': json.loads(json.dumps(wiz.generate_data(), default=str))}
        response = _FakeResponse()
        wiz.get_xlsx_report(data, response)
        self.assertTrue(response.stream.buffer.getvalue().startswith(b'PK'))
        report = self.env['report.hotel_management_odoo.report_sale_order']
        self.assertEqual(report._get_report_values([], {'booking': [2]}), {'booking': [2]})
        self.assertEqual(report._get_report_values([]), {'booking': []})

    # ---- compute.bill ----
    def test_compute_bill_lines(self):
        food = self._make_food()
        booking = self._make_booking(
            rooms=self.room2,
            food_order_line_ids=[Command.create({'food_id': food.id})],
            service_line_ids=[Command.create({'service_id': self.service.id})],
            vehicle_line_ids=[Command.create({'fleet_id': self._make_vehicle('V2').id})])
        wiz = self.env['compute.bill'].create({'booking_id': booking.id})
        self.assertEqual(wiz.room_line_ids, booking.room_line_ids)
        self.assertEqual(wiz.food_line_ids, booking.food_order_line_ids)
        self.assertEqual(wiz.service_line_ids, booking.service_line_ids)
        self.assertEqual(wiz.fleet_line_ids, booking.vehicle_line_ids)
        self.assertFalse(wiz.event_line_ids)
        self.assertFalse(wiz.pos_order_ids)
        self.assertEqual(wiz.bill_type, 'combined')
        self.assertEqual(wiz.partner_id, self.partner)

    def test_compute_bill_print(self):
        wiz = self.env['compute.bill'].create({'booking_id': self.booking.id})
        # Skip the external report layout configuration wizard that Odoo
        # returns for an admin whose company has no report layout yet.
        action = wiz.with_context(discard_logo_check=True).action_print_bill()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_name'], 'hotel_management_odoo.report_combined_bill')

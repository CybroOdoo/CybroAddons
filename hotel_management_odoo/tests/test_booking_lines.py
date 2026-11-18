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

from odoo import fields
from odoo.tests import tagged

from .common import HotelCommon


@tagged('post_install', '-at_install')
class TestBookingLines(HotelCommon):

    def test_room_line_onchange_quantity(self):
        now = fields.Datetime.now()
        line = self.env['room.booking.line'].new({
            'room_id': self.room1.id,
            'checkin_date': now,
            'checkout_date': now + timedelta(days=2, hours=1)})
        line._onchange_checkin_date()
        self.assertEqual(line.uom_qty, 3)
        line.checkout_date = now + timedelta(days=2)
        line._onchange_checkin_date()
        self.assertEqual(line.uom_qty, 2)
        line.checkout_date = now
        line._onchange_checkin_date()
        self.assertEqual(line.uom_qty, 0)

    def test_room_line_price_unit(self):
        booking = self._make_booking(days=3)
        line = booking.room_line_ids
        self.assertAlmostEqual(line.price_unit, 100.0)
        self.assertAlmostEqual(line.price_subtotal, 300.0)
        self.assertAlmostEqual(line.price_total, 300.0)
        self.assertAlmostEqual(line.price_tax, 0.0)
        self.assertEqual(line.uom_id, self.env.ref('uom.product_uom_day'))

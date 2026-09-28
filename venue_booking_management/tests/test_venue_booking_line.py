# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase
from odoo import fields
from datetime import timedelta

class TestVenueBookingLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.amenity = cls.env['amenities'].create({'name': 'Chair', 'amount': 2.0})
        cls.venue_type = cls.env['venue.type'].create({'name': 'Small Room'})
        cls.venue = cls.env['venue'].create({
            'name': 'Room A',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'East Wing',
            'capacity': 10,
            'seating': 10,
            'venue_charge_hour': 10.0,
            'venue_charge_day': 100.0,
        })
        cls.booking = cls.env['venue.booking'].create({
            'partner_id': cls.partner.id,
            'venue_id': cls.venue.id,
            'start_date': fields.Datetime.now(),
            'end_date': fields.Datetime.now() + timedelta(hours=2),
            'booking_type': 'hour',
        })
        cls.booking_line = cls.env['venue.booking.line'].create({
            'venue_booking_id': cls.booking.id,
            'amenity_id': cls.amenity.id,
            'quantity': 10,
            'is_included': False,
        })

    def test_venue_booking_line_sub_total(self):
        """Test sub total computation for venue booking line."""
        self.assertEqual(self.booking_line.sub_total, 20.0)

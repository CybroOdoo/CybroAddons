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
"""Test cases for venue.booking.report SQL view model."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestVenueBookingReport(TransactionCase):
    """Test suite for venue.booking.report view."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueType = cls.env['venue.type']
        cls.Partner = cls.env['res.partner']
        cls.VenueBooking = cls.env['venue.booking']
        cls.BookingReport = cls.env['venue.booking.report']

        cls.venue_type = cls.VenueType.create({'name': 'Pavilion'})
        cls.venue = cls.Venue.create({
            'name': 'Sunset Pavilion',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'Sunset Beach',
        })
        cls.partner = cls.Partner.create({'name': 'Customer D'})

    def test_venue_booking_report_view(self):
        """Test venue.booking.report view queries confirmed bookings."""
        booking = self.VenueBooking.create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': '2026-11-15 09:00:00',
            'end_date': '2026-11-15 18:00:00',
        })
        # Draft booking should not appear in report view
        self.env.flush_all()
        report_record = self.BookingReport.search([('id', '=', booking.id)])
        self.assertFalse(report_record)

        # Confirm booking -> now appears in report view
        booking.action_booking_confirm()
        self.env.flush_all()
        report_record = self.BookingReport.search([('id', '=', booking.id)])
        self.assertTrue(report_record)
        self.assertEqual(report_record.partner_id.id, self.partner.id)
        self.assertEqual(report_record.state, 'confirm')

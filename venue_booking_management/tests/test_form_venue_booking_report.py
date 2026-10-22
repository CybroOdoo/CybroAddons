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
"""Test cases for PDF report parser report.venue_booking_management.report_venue_booking."""
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestFormVenueBookingReport(TransactionCase):
    """Test suite for venue booking PDF report parser."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueType = cls.env['venue.type']
        cls.Partner = cls.env['res.partner']
        cls.VenueBooking = cls.env['venue.booking']
        cls.ReportModel = cls.env['report.venue_booking_management.report_venue_booking']

        cls.venue_type = cls.VenueType.create({'name': 'Theatre'})
        cls.venue = cls.Venue.create({
            'name': 'Broadway Hall',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'Broadway Street',
        })
        cls.partner = cls.Partner.create({'name': 'Customer C'})

        cls.booking = cls.VenueBooking.create({
            'partner_id': cls.partner.id,
            'venue_id': cls.venue.id,
            'start_date': '2026-11-01 09:00:00',
            'end_date': '2026-11-02 18:00:00',
        })

    def test_report_values_with_docids(self):
        """Test report values when docids are provided."""
        values = self.ReportModel._get_report_values([self.booking.id])
        self.assertIn('doc_ids', values)
        self.assertIn('today_date', values)
        self.assertEqual(values['doc_ids'].id, self.booking.id)

    def test_report_values_with_data_form(self):
        """Test report values when called from wizard with data['form']."""
        form_data = {
            'venue_id': [self.venue.id, self.venue.name],
            'partner_id': [self.partner.id, self.partner.name],
            'start_date': '2026-11-01',
            'end_date': '2026-11-05',
        }
        data = {'form': form_data}
        values = self.ReportModel._get_report_values([], data=data)
        self.assertIn('docs', values)
        self.assertIn('docs2', values)
        self.assertIn('today_date', values)
        self.assertEqual(values['docs2'], form_data)

    def test_report_values_date_validation(self):
        """Test report parser raises ValidationError when start_date > end_date."""
        form_data = {
            'start_date': '2026-11-10',
            'end_date': '2026-11-01',
        }
        data = {'form': form_data}
        with self.assertRaises(ValidationError):
            self.ReportModel._get_report_values([], data=data)

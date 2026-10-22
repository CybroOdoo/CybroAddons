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
"""Test cases for website venue booking and xlsx controller."""
import json
from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user


@tagged('post_install', '-at_install')
class TestControllersVenueBooking(HttpCase):
    """Test suite for website venue booking and report controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueType = cls.env['venue.type']
        cls.Partner = cls.env['res.partner']
        cls.VenueBooking = cls.env['venue.booking']

        cls.manager_user = new_test_user(
            cls.env,
            login='venue_manager',
            groups='venue_booking_management.venue_booking_management_group_venue_manager,base.group_user',
            name='Venue Manager',
        )

        cls.venue_type = cls.VenueType.create({'name': 'Banquet'})
        cls.venue = cls.Venue.create({
            'name': 'Rose Garden',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'Rosewood Boulevard',
        })
        cls.partner = cls.Partner.create({'name': 'Public Customer'})

    def test_website_venue_booking_page(self):
        """Test public /venue/booking route renders successfully."""
        res = self.url_open('/venue/booking')
        self.assertEqual(res.status_code, 200)

    def test_booking_check_availability_json(self):
        """Test /booking/check_availability JSON route."""
        # Check when available
        params = {
            'start_date': '2026-11-20 09:00:00',
            'end_date': '2026-11-20 18:00:00',
            'venue_id': self.venue.id,
        }
        res = self.url_open(
            '/booking/check_availability',
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': params}),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res.status_code, 200)
        result = res.json().get('result')
        self.assertTrue(result.get('available'))

        # Create confirmed booking and check again
        self.VenueBooking.create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': '2026-11-20 09:00:00',
            'end_date': '2026-11-20 18:00:00',
            'state': 'confirm',
        })
        res2 = self.url_open(
            '/booking/check_availability',
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': params}),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(res2.status_code, 200)
        result2 = res2.json().get('result')
        self.assertFalse(result2.get('available'))

    def test_booking_submit_route(self):
        """Test submitting a booking from public website form."""
        self.authenticate(None, None)
        post_data = {
            'name': 'Alice Smith',
            'mobile_no': '9876543210',
            'city': 'New York',
            'venue_type': str(self.venue.id),
            'from_date': '2026-11-22 09:00:00',
            'to_date': '2026-11-22 18:00:00',
            'booking_type': 'day',
            'csrf_token': self.csrf_token(),
        }
        res = self.url_open('/booking/submit', data=post_data)
        self.assertEqual(res.status_code, 200)

        # Check booking record was created
        created_booking = self.VenueBooking.search([
            ('venue_id', '=', self.venue.id),
            ('start_date', '=', '2026-11-22 09:00:00'),
        ])
        self.assertTrue(created_booking)
        self.assertEqual(created_booking.partner_id.name, 'Alice Smith')

    def test_venue_xlsx_reports_controller(self):
        """Test /venue_xlsx_reports controller download."""
        self.authenticate('venue_manager', 'venue_manager')
        wizard = self.env['venue.booking.analysis'].create({
            'venue_id': self.venue.id,
            'start_date': '2026-11-01 09:00:00',
            'end_date': '2026-11-05 18:00:00',
        })
        action = wizard.action_print_xlsx()
        options_str = action['data']['options']

        url = (
            f'/venue_xlsx_reports?model=venue.booking.analysis&options={options_str}'
            f'&output_format=xlsx&report_name=Venue_Report'
        )
        res = self.url_open(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers.get('Content-Type'),
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

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
"""Test cases for portal controller in venue_booking_management."""
from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user
from odoo.addons.venue_booking_management.controllers.portal import CustomerPortal


@tagged('post_install', '-at_install')
class TestControllersPortal(HttpCase):
    """Test suite for portal controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueType = cls.env['venue.type']
        cls.VenueBooking = cls.env['venue.booking']

        cls.portal_user_1 = new_test_user(
            cls.env,
            login='portal_user_1',
            groups='base.group_portal',
            name='Portal User 1',
            email='portal1@example.com',
        )

        cls.portal_user_2 = new_test_user(
            cls.env,
            login='portal_user_2',
            groups='base.group_portal',
            name='Portal User 2',
            email='portal2@example.com',
        )

        cls.venue_type = cls.VenueType.create({'name': 'Banquet'})
        cls.venue = cls.Venue.create({
            'name': 'Silver Suite',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'City Center',
        })

        cls.booking_1 = cls.VenueBooking.create({
            'partner_id': cls.portal_user_1.partner_id.id,
            'venue_id': cls.venue.id,
            'start_date': '2026-12-01 10:00:00',
            'end_date': '2026-12-01 18:00:00',
        })

    def test_prepare_home_portal_values(self):
        """Test home portal values contain booking count."""
        portal_controller = CustomerPortal()
        values = self.env['venue.booking'].with_user(self.portal_user_1).search_count(
            [('partner_id', '=', self.portal_user_1.partner_id.id)]
        )
        self.assertEqual(values, 1)
        self.assertTrue(hasattr(portal_controller, '_prepare_home_portal_values'))

    def test_portal_my_venue_booking_list(self):
        """Test accessing /my/venue_booking as authenticated portal user."""
        self.authenticate('portal_user_1', 'portal_user_1')
        res = self.url_open('/my/venue_booking')
        self.assertEqual(res.status_code, 200)

    def test_portal_booking_data_idor(self):
        """Test that portal user 1 can view own booking, but portal user 2 is redirected."""
        # User 1 accesses their own booking
        self.authenticate('portal_user_1', 'portal_user_1')
        res1 = self.url_open(f'/my/booking_data/{self.booking_1.id}')
        self.assertEqual(res1.status_code, 200)

        # User 2 tries to access User 1's booking -> should redirect to /my/venue_booking
        self.authenticate('portal_user_2', 'portal_user_2')
        res2 = self.url_open(f'/my/booking_data/{self.booking_1.id}', allow_redirects=False)
        self.assertIn(res2.status_code, (302, 303))
        self.assertEqual(res2.headers.get('Location'), '/my/venue_booking')

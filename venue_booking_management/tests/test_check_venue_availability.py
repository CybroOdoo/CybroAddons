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
"""Test cases for check.venue.availability wizard."""
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCheckVenueAvailability(TransactionCase):
    """Test suite for check.venue.availability."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueType = cls.env['venue.type']
        cls.Partner = cls.env['res.partner']
        cls.Wizard = cls.env['check.venue.availability']
        cls.VenueBooking = cls.env['venue.booking']

        cls.venue_type = cls.VenueType.create({'name': 'Conference'})
        cls.venue = cls.Venue.create({
            'name': 'Sapphire Hall',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'Uptown',
            'capacity': 100,
            'venue_charge_day': 500.0,
            'additional_charge_day': 50.0,
        })
        cls.partner = cls.Partner.create({'name': 'Customer A'})

    def test_availability_success(self):
        """Test search venue returns form action when available."""
        wizard = self.Wizard.create({
            'venue_id': self.venue.id,
            'booking_type': 'day',
            'start_date': '2026-11-20 09:00:00',
            'end_date': '2026-11-20 18:00:00',
            'capacity': 50,
            'budget': 1000.0,
        })
        action = wizard.action_search_venue()
        self.assertEqual(action.get('res_model'), 'venue.booking')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')

    def test_availability_date_overlap_error(self):
        """Test raises ValidationError when venue is already booked."""
        self.VenueBooking.create({
            'partner_id': self.partner.id,
            'venue_id': self.venue.id,
            'start_date': '2026-11-20 09:00:00',
            'end_date': '2026-11-20 18:00:00',
            'state': 'confirm',
        })
        wizard = self.Wizard.create({
            'venue_id': self.venue.id,
            'booking_type': 'day',
            'start_date': '2026-11-20 10:00:00',
            'end_date': '2026-11-20 12:00:00',
            'capacity': 50,
        })
        with self.assertRaises(ValidationError):
            wizard.action_search_venue()

    def test_availability_capacity_error(self):
        """Test raises ValidationError when requested capacity exceeds venue."""
        wizard = self.Wizard.create({
            'venue_id': self.venue.id,
            'booking_type': 'day',
            'start_date': '2026-11-25 09:00:00',
            'end_date': '2026-11-25 18:00:00',
            'capacity': 150,  # Venue capacity is 100
        })
        with self.assertRaises(ValidationError):
            wizard.action_search_venue()

    def test_availability_budget_error(self):
        """Test raises ValidationError when venue charge exceeds budget."""
        wizard = self.Wizard.create({
            'venue_id': self.venue.id,
            'booking_type': 'day',
            'start_date': '2026-11-25 09:00:00',
            'end_date': '2026-11-25 18:00:00',
            'capacity': 50,
            'budget': 200.0,  # Venue is 500 + 50 = 550
        })
        with self.assertRaises(ValidationError):
            wizard.action_search_venue()

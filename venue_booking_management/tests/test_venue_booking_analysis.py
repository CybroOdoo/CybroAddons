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
"""Test cases for venue.booking.analysis wizard."""
import json
from unittest.mock import MagicMock
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestVenueBookingAnalysis(TransactionCase):
    """Test suite for venue.booking.analysis wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Venue = cls.env['venue']
        cls.VenueType = cls.env['venue.type']
        cls.Partner = cls.env['res.partner']
        cls.AnalysisWizard = cls.env['venue.booking.analysis']

        cls.venue_type = cls.VenueType.create({'name': 'Banquet'})
        cls.venue = cls.Venue.create({
            'name': 'Crystal Room',
            'venue_type_id': cls.venue_type.id,
            'venue_location': 'Floor 1',
        })
        cls.partner = cls.Partner.create({'name': 'Customer B'})

    def test_date_validation(self):
        """Test validation error when start_date > end_date."""
        wizard = self.AnalysisWizard.create({
            'start_date': '2026-12-10 18:00:00',
            'end_date': '2026-12-10 09:00:00',
        })
        with self.assertRaises(ValidationError):
            wizard.action_print_pdf()

        with self.assertRaises(ValidationError):
            wizard.action_print_xlsx()

    def test_action_print_pdf(self):
        """Test action_print_pdf returns report action with serialized data."""
        wizard = self.AnalysisWizard.create({
            'venue_id': self.venue.id,
            'partner_id': self.partner.id,
            'start_date': '2026-12-01 09:00:00',
            'end_date': '2026-12-05 18:00:00',
        })
        action = wizard.with_context(discard_logo_check=True).action_print_pdf()
        self.assertIsInstance(action, dict)
        if action.get('type') == 'ir.actions.report':
            form_data = action.get('data', {}).get('form', {})
        else:
            form_data = action.get('context', {}).get('report_action', {}).get('data', {}).get('form', {})
        self.assertEqual(form_data.get('venue_id', [False])[0], self.venue.id)

    def test_action_print_xlsx_and_generator(self):
        """Test action_print_xlsx and get_xlsx_report generation."""
        wizard = self.AnalysisWizard.create({
            'venue_id': self.venue.id,
            'partner_id': self.partner.id,
            'start_date': '2026-12-01 09:00:00',
            'end_date': '2026-12-05 18:00:00',
        })
        action = wizard.action_print_xlsx()
        self.assertEqual(action.get('report_type'), 'xlsx')
        options = json.loads(action['data']['options'])

        # Mock HTTP response to test get_xlsx_report
        response = MagicMock()
        wizard.get_xlsx_report(options, response)
        self.assertTrue(response.stream.write.called)

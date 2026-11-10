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
"""Test suite for res.config.settings table reservation configurations."""
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for table reservation configuration settings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Settings POS',
            'module_pos_restaurant': True,
        })

    def test_set_and_get_values_valid(self):
        """Test setting and retrieving valid configuration values."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'is_lead_time': True,
            'reservation_lead_time': 3.5,
            'refund': 'Full refund before 24 hours',
            'pos_set_opening_hours': True,
            'pos_opening_hour': 9.0,
            'pos_closing_hour': 23.0,
        })
        settings.set_values()

        values = settings.get_values()
        self.assertTrue(values.get('is_lead_time'))
        self.assertAlmostEqual(values.get('reservation_lead_time'), 3.5)
        self.assertEqual(values.get('refund'), 'Full refund before 24 hours')

    def test_set_values_invalid_lead_time(self):
        """Test that invalid reservation lead time raises ValidationError."""
        settings = self.env['res.config.settings'].create({
            'is_lead_time': True,
            'reservation_lead_time': 25.0,
        })
        with self.assertRaises(ValidationError):
            settings.set_values()

        settings_neg = self.env['res.config.settings'].create({
            'is_lead_time': True,
            'reservation_lead_time': -1.0,
        })
        with self.assertRaises(ValidationError):
            settings_neg.set_values()

    def test_set_values_invalid_opening_closing_hours(self):
        """Test that invalid opening and closing hours raise ValidationError."""
        settings_open = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_set_opening_hours': True,
            'pos_opening_hour': 25.5,
            'pos_closing_hour': 20.0,
        })
        with self.assertRaises(ValidationError):
            settings_open.set_values()

        settings_close = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_set_opening_hours': True,
            'pos_opening_hour': 8.0,
            'pos_closing_hour': -0.5,
        })
        with self.assertRaises(ValidationError):
            settings_close.set_values()


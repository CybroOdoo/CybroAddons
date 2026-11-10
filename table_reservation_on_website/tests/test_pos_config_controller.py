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
"""Test suite for POS config controller."""
from odoo.tests import TransactionCase, tagged
from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.table_reservation_on_website.controllers.pos_config import ResConfigSettingsController


@tagged('post_install', '-at_install')
class TestPosConfigController(TransactionCase):
    """Test pos config controller endpoints and helpers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = ResConfigSettingsController()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Controller POS',
            'module_pos_restaurant': True,
            'set_opening_hours': True,
            'opening_hour': 9.5,
            'closing_hour': 22.0,
        })

    def test_float_to_time(self):
        """Test float_to_time hour conversions."""
        self.assertEqual(self.controller.float_to_time(0.0), '00:00')
        self.assertEqual(self.controller.float_to_time(8.5), '08:30')
        self.assertEqual(self.controller.float_to_time(14.25), '14:15')
        self.assertEqual(self.controller.float_to_time(23.75), '23:45')

    def test_get_opening_closing_hours_active(self):
        """Test get_opening_closing_hours with restaurant POS configured."""
        self.env['ir.config_parameter'].sudo().set_bool(
            'table_reservation_on_website.is_lead_time', True)
        self.env['ir.config_parameter'].sudo().set_float(
            'table_reservation_on_website.reservation_lead_time', 2.0)

        with MockRequest(self.env):
            result = self.controller.get_opening_closing_hours()
            self.assertEqual(result.get('opening_hour'), '09:30')
            self.assertEqual(result.get('closing_hour'), '22:00')
            self.assertTrue(result.get('is_lead_time'))
            self.assertAlmostEqual(result.get('reservation_lead_time'), 2.0)

    def test_get_opening_closing_hours_no_opening_hours(self):
        """Test get_opening_closing_hours when set_opening_hours is False."""
        self.pos_config.write({'set_opening_hours': False})
        with MockRequest(self.env):
            result = self.controller.get_opening_closing_hours()
            self.assertEqual(result.get('opening_hour'), '00:00')
            self.assertEqual(result.get('closing_hour'), '24:00')

    def test_get_opening_closing_hours_no_pos(self):
        """Test get_opening_closing_hours when no restaurant POS exists."""
        self.pos_config.unlink()
        with MockRequest(self.env):
            result = self.controller.get_opening_closing_hours()
            self.assertIn('error', result)


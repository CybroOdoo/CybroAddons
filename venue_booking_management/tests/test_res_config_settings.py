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
"""Test cases for res.config.settings venue booking settings."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for res.config.settings venue booking parameters."""

    def test_config_settings_extra_charge(self):
        """Test configuring extra charge and amount parameters."""
        settings = self.env['res.config.settings'].create({
            'is_extra': True,
            'extra_amount': 25.5,
        })
        settings.execute()

        config_sudo = self.env['ir.config_parameter'].sudo()
        self.assertEqual(config_sudo.get_str('venue_booking_management.is_extra'), 'True')
        self.assertEqual(config_sudo.get_float('venue_booking_management.extra_amount'), 25.5)

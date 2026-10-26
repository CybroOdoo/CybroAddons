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
"""Test suite for res.config.settings extension."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for packers and movers configuration settings."""

    def test_pricing_and_distance_settings(self):
        """Test configuring distance amount, extra amount, and distance limit."""
        settings = self.env['res.config.settings'].create({
            'distance_amount': 25.0,
            'is_extra': True,
            'extra_amount': 1.2,
            'is_distance_limited': True,
            'max_distance': 500.0,
        })
        settings.execute()

        ICP = self.env['ir.config_parameter'].sudo()
        self.assertAlmostEqual(
            ICP.get_float('packers_and_movers_management.distance_amount'), 25.0)
        is_extra_key = self.env['res.config.settings']._fields['is_extra'].config_parameter or 'packers_and_movers_management.is_extra'
        extra_amount_key = self.env['res.config.settings']._fields['extra_amount'].config_parameter or 'packers_and_movers_management.extra_amount'
        self.assertTrue(ICP.get_bool(is_extra_key))
        self.assertAlmostEqual(ICP.get_float(extra_amount_key), 1.2)
        self.assertTrue(
            ICP.get_bool('packers_and_movers_management.is_distance_limited'))
        self.assertAlmostEqual(
            ICP.get_float('packers_and_movers_management.max_distance'), 500.0)

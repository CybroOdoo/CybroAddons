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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Tests for the internal reference generator settings."""
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import PARAM_PREFIX, InternalRefCommon


@tagged('post_install', '-at_install')
class TestResConfigSettings(InternalRefCommon):
    """The settings are stored in and read from the config parameters."""

    def test_01_settings_saved_and_loaded(self):
        """Saving the settings stores every value in the parameters."""
        self.env['res.config.settings'].create({
            'auto_generate_internal_ref': False,
            'product_name_config': True,
            'pro_name_digit': 4,
            'pro_name_separator': '#',
            'pro_categ_config': False,
            'pro_categ_digit': 2,
            'pro_categ_separator': '*',
            'pro_template_config': True,
            'pro_template_digit': 1,
            'pro_template_separator': '.',
        }).execute()
        param = self.config_parameter
        self.assertFalse(param.get_bool(
            PARAM_PREFIX + 'auto_generate_internal_ref'))
        self.assertEqual(param.get_int(PARAM_PREFIX + 'pro_name_digit'), 4)
        self.assertEqual(
            param.get_str(PARAM_PREFIX + 'pro_name_separator'), '#')
        self.assertEqual(
            param.get_str(PARAM_PREFIX + 'pro_template_separator'), '.')
        settings = self.env['res.config.settings'].create({})
        self.assertEqual(settings.pro_categ_digit, 2)
        self.assertEqual(settings.pro_categ_separator, '*')
        self.assertTrue(settings.pro_template_config)

    def test_02_enabled_part_needs_digits(self):
        """An enabled part with 0 characters is refused."""
        for enabled, digit in (('product_name_config', 'pro_name_digit'),
                               ('pro_categ_config', 'pro_categ_digit'),
                               ('pro_template_config', 'pro_template_digit')):
            with self.assertRaises(ValidationError):
                self.env['res.config.settings'].create({
                    enabled: True, digit: 0})

    def test_03_disabled_part_allows_zero(self):
        """A disabled part may keep 0 characters."""
        settings = self.env['res.config.settings'].create({
            'product_name_config': False, 'pro_name_digit': 0,
            'pro_categ_config': False, 'pro_categ_digit': 0,
            'pro_template_config': False, 'pro_template_digit': 0,
        })
        self.assertEqual(settings.pro_name_digit, 0)

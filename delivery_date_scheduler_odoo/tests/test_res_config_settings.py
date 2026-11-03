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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for delivery date scheduler configuration settings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_parameter = cls.env['ir.config_parameter'].sudo()

    def setUp(self):
        super().setUp()
        self.config_parameter.search([
            ('key', 'like', 'delivery_date_scheduler_odoo.%')
        ]).unlink()

    def test_default_values(self):
        """Test default values of delivery date scheduler settings fields."""
        settings = self.env['res.config.settings'].create({})
        self.assertFalse(settings.warning_date, "warning_date should default to False")
        self.assertEqual(settings.min_date_range, 5, "min_date_range should default to 5")
        self.assertEqual(settings.max_date_range, 10, "max_date_range should default to 10")

    def test_set_and_get_values(self):
        """Test setting and getting configuration parameters via res.config.settings."""
        settings = self.env['res.config.settings'].create({
            'warning_date': True,
            'min_date_range': 3,
            'max_date_range': 15,
        })
        settings.execute()

        # Verify values stored in ir.config_parameter
        self.assertEqual(
            self.config_parameter.get_str('delivery_date_scheduler_odoo.warning_date'),
            'True',
            "warning_date config parameter should be stored as 'True'",
        )
        self.assertEqual(
            self.config_parameter.get_str('delivery_date_scheduler_odoo.min_date_range'),
            '3',
            "min_date_range config parameter should be stored as '3'",
        )
        self.assertEqual(
            self.config_parameter.get_str('delivery_date_scheduler_odoo.max_date_range'),
            '15',
            "max_date_range config parameter should be stored as '15'",
        )

        # Instantiate a new settings record to test get_values retrieval
        new_settings = self.env['res.config.settings'].create({})
        self.assertTrue(new_settings.warning_date, "Loaded warning_date should be True")
        self.assertEqual(new_settings.min_date_range, 3, "Loaded min_date_range should be 3")
        self.assertEqual(new_settings.max_date_range, 15, "Loaded max_date_range should be 15")

    def test_disable_warning_date(self):
        """Test toggling warning_date from True back to False."""
        settings_enabled = self.env['res.config.settings'].create({
            'warning_date': True,
            'min_date_range': 4,
            'max_date_range': 8,
        })
        settings_enabled.execute()
        self.assertEqual(
            self.config_parameter.get_str('delivery_date_scheduler_odoo.warning_date'),
            'True',
        )

        # Disable warning_date
        settings_disabled = self.env['res.config.settings'].create({
            'warning_date': False,
        })
        settings_disabled.execute()
        self.assertEqual(
            self.config_parameter.get_str('delivery_date_scheduler_odoo.warning_date'),
            'False',
            "warning_date should be stored as 'False' after disabling",
        )

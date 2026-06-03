# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    def setUp(self):
        super(TestResConfigSettings, self).setUp()
        self.config_settings = self.env['res.config.settings'].create({})
        _logger.info("--- TestResConfigSettings: setUp completed. Initialized res.config.settings record ---")

    def test_is_tender_sales_config(self):
        """Test enabling and disabling the is_tender_sales configuration setting."""
        _logger.info("--- Starting test_is_tender_sales_config ---")

        # Check initial state from config parameter
        initial_param = self.env['ir.config_parameter'].sudo().get_param('tender_sales.is_tender_sales')
        initial_bool = bool(initial_param == 'True')
        _logger.info("Initial setting value: %s (param: %s)", initial_bool, initial_param)

        self.assertEqual(
            self.config_settings.is_tender_sales,
            initial_bool,
            "Initial setting value does not match the config parameter state"
        )

        # Enable sale agreements setting
        _logger.info("Enabling is_tender_sales (setting to True)...")
        self.config_settings.is_tender_sales = True
        self.config_settings.execute()

        # Verify it has been updated to True in ir.config_parameter
        updated_param = self.env['ir.config_parameter'].sudo().get_param('tender_sales.is_tender_sales')
        _logger.info("Value after execution: %s", updated_param)
        self.assertEqual(updated_param, 'True', "Config parameter was not set to 'True'")

        # Verify reading the settings model returns True
        new_config = self.env['res.config.settings'].create({})
        _logger.info("Verifying configuration: is_tender_sales in new config: %s", new_config.is_tender_sales)
        self.assertTrue(new_config.is_tender_sales, "is_tender_sales should be True in new config record")

        # Disable sale agreements setting
        _logger.info("Disabling is_tender_sales (setting to False)...")
        new_config.is_tender_sales = False
        new_config.execute()

        # Verify it has been updated to False (or empty string/None) in ir.config_parameter
        final_param = self.env['ir.config_parameter'].sudo().get_param('tender_sales.is_tender_sales')
        _logger.info("Value after disabling: %s", final_param)
        self.assertNotEqual(final_param, 'True', "Config parameter was not removed/disabled")

        # Verify reading again returns False
        final_config = self.env['res.config.settings'].create({})
        _logger.info("Verifying configuration: is_tender_sales in final config: %s", final_config.is_tender_sales)
        self.assertFalse(final_config.is_tender_sales, "is_tender_sales should be False")

        _logger.info("--- Completed test_is_tender_sales_config successfully ---")

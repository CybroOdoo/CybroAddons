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
"""Test cases for res.config.settings Google Gemini AI configuration."""
from unittest.mock import patch
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for Gemini configuration parameters and connection actions."""

    def test_gemini_config_settings_storage(self):
        """Test configuring and retrieving Gemini API key and model parameters."""
        settings = self.env['res.config.settings'].create({
            'gemini_api_key': 'AIzaSyTestApiKey12345',
            'gemini_model': 'gemini-3.6-pro',
        })
        settings.execute()

        config_sudo = self.env['ir.config_parameter'].sudo()
        self.assertEqual(
            config_sudo.get_str('predict_late_payment.gemini_api_key'),
            'AIzaSyTestApiKey12345',
        )
        self.assertEqual(
            config_sudo.get_str('predict_late_payment.gemini_model'),
            'gemini-3.6-pro',
        )

    def test_gemini_action_get_key(self):
        """Test that action_get_gemini_key returns URL action for AI Studio."""
        settings = self.env['res.config.settings'].new()
        action = settings.action_get_gemini_key()
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('url'), 'https://aistudio.google.com/apikey')

    def test_gemini_test_connection_action(self):
        """Test connection action returns display_notification client action."""
        settings = self.env['res.config.settings'].new()
        action = settings.action_test_gemini_connection()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')

    def test_get_values_deprecated_model(self):
        """Test get_values converts deprecated model to gemini-3.6-flash."""
        with patch(
            'odoo.addons.base.models.res_config.ResConfigSettings.get_values',
            return_value={'gemini_model': 'gemini-2.5-flash'},
        ):
            settings = self.env['res.config.settings'].new()
            vals = settings.get_values()
            self.assertEqual(vals.get('gemini_model'), 'gemini-3.6-flash')


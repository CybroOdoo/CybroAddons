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
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'at_install')
class TestResConfigSettings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()

    def _set_config(self, key, value):
        params = self.config_param
        if hasattr(params, 'set_str'):
            params.set_str(key, value)
        elif hasattr(params, 'set_param'):
            params.set_param(key, value)

    def _get_config(self, key):
        params = self.config_param
        if hasattr(params, 'get_str'):
            return params.get_str(key)
        if hasattr(params, 'get_param'):
            return params.get_param(key)
        return False

    def test_res_config_settings_crud(self):
        """Test setting and getting configuration parameters via settings transient model."""
        settings = self.env['res.config.settings'].create({
            'gemini_api_key': 'TestApiKey456',
            'gemini_model': 'gemini-3.8-flash',
            'address_autofill': True,
        })
        settings.execute()

        val_key = self._get_config('ai_address_autofill.gemini_api_key')
        self.assertEqual(val_key, 'TestApiKey456')

        val_model = self._get_config('ai_address_autofill.gemini_model')
        self.assertEqual(val_model, 'gemini-3.8-flash')

        val_autofill = self._get_config('ai_address_autofill.address_autofill')
        self.assertIn(str(val_autofill).lower(), ('true', '1'))

    def test_action_test_gemini_connection_missing_key(self):
        """Test test connection action returns warning when API key is missing."""
        self._set_config('ai_address_autofill.gemini_api_key', '')
        settings = self.env['res.config.settings'].create({
            'gemini_api_key': False,
        })
        action = settings.action_test_gemini_connection()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action['params']['type'], 'warning')
        self.assertIn("enter an API Key", action['params']['message'])

    def test_action_test_gemini_connection_success(self):
        """Test test connection action returns success notification when Gemini service succeeds."""
        settings = self.env['res.config.settings'].create({
            'gemini_api_key': 'TestKey789',
            'gemini_model': 'gemini-3.5-flash',
        })
        with patch.object(type(self.env['gemini.service']), 'test_connection', return_value=(True, "Connected successfully")):
            action = settings.action_test_gemini_connection()
            self.assertEqual(action['params']['type'], 'success')
            self.assertEqual(action['params']['title'], 'Connection Successful')

    def test_action_test_gemini_connection_failure(self):
        """Test test connection action returns danger notification when Gemini service fails."""
        settings = self.env['res.config.settings'].create({
            'gemini_api_key': 'BadKey',
            'gemini_model': 'gemini-3.5-flash',
        })
        with patch.object(type(self.env['gemini.service']), 'test_connection', return_value=(False, "Invalid API key")):
            action = settings.action_test_gemini_connection()
            self.assertEqual(action['params']['type'], 'danger')
            self.assertEqual(action['params']['title'], 'Connection Failed')

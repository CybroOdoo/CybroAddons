# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

from unittest.mock import patch
import requests
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestResConfigSettings(TransactionCase):

    def setUp(self):
        super(TestResConfigSettings, self).setUp()
        self.Settings = self.env['res.config.settings']

    def test_settings_get_set_values(self):
        """Test that settings get and set values correctly."""
        settings_record = self.Settings.create({
            'enable_ai_sentiment': True,
            'openai_api_key': 'test_key_123',
            'model_id': 'gpt-4o-mini',
        })
        settings_record.set_values()

        # Retrieve values and assert they are set in ir.config_parameter
        values = settings_record.get_values()
        self.assertTrue(values['enable_ai_sentiment'])
        self.assertEqual(values['openai_api_key'], 'test_key_123')
        self.assertEqual(values['model_id'], 'gpt-4o-mini')

        # Test validation error when enable_ai_sentiment is True but api key is missing
        with self.assertRaises(ValidationError):
            settings_record.write({
                'enable_ai_sentiment': True,
                'openai_api_key': '',
            })
            settings_record.set_values()

    @patch('requests.get')
    def test_action_test_openai_connection_success(self, mock_get):
        """Test action_test_openai_connection when the connection is successful (HTTP 200)."""
        mock_get.return_value.status_code = 200
        settings_record = self.Settings.create({
            'openai_api_key': 'valid_key_123',
        })
        action = settings_record.action_test_openai_connection()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action.get('params', {}).get('type'), 'success')

    @patch('requests.get')
    def test_action_test_openai_connection_invalid_key(self, mock_get):
        """Test action_test_openai_connection raises ValidationError when key is invalid (HTTP 401)."""
        mock_get.return_value.status_code = 401
        settings_record = self.Settings.create({
            'openai_api_key': 'invalid_key',
        })
        with self.assertRaises(ValidationError) as cm:
            settings_record.action_test_openai_connection()
        self.assertIn("Invalid OpenAI API Key.", str(cm.exception))

    @patch('requests.get')
    def test_action_test_openai_connection_failure(self, mock_get):
        """Test action_test_openai_connection raises ValidationError when API returns a non-200 / non-401 code."""
        mock_get.return_value.status_code = 500
        mock_get.return_value.text = "Internal Server Error"
        settings_record = self.Settings.create({
            'openai_api_key': 'some_key',
        })
        with self.assertRaises(ValidationError) as cm:
            settings_record.action_test_openai_connection()
        self.assertIn("OpenAI Error (500)", str(cm.exception))

    @patch('requests.get')
    def test_action_test_openai_connection_timeout(self, mock_get):
        """Test action_test_openai_connection raises ValidationError on request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        settings_record = self.Settings.create({
            'openai_api_key': 'some_key',
        })
        with self.assertRaises(ValidationError) as cm:
            settings_record.action_test_openai_connection()
        self.assertIn("OpenAI connection timed out.", str(cm.exception))

    @patch('requests.get')
    def test_action_test_openai_connection_error(self, mock_get):
        """Test action_test_openai_connection raises ValidationError on connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection Error")
        settings_record = self.Settings.create({
            'openai_api_key': 'some_key',
        })
        with self.assertRaises(ValidationError) as cm:
            settings_record.action_test_openai_connection()
        self.assertIn("Cannot connect to OpenAI servers.", str(cm.exception))

    def test_action_test_openai_connection_missing_key(self):
        """Test action_test_openai_connection raises ValidationError if no API key is provided."""
        settings_record = self.Settings.create({
            'openai_api_key': False,
        })
        with self.assertRaises(ValidationError) as cm:
            settings_record.action_test_openai_connection()
        self.assertIn("Please enter an OpenAI API key.", str(cm.exception))

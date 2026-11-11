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
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', 'at_install')
class TestGeminiService(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = cls.env['gemini.service']
        cls.config_param = cls.env['ir.config_parameter'].sudo()

    def _set_config(self, key, value):
        params = self.config_param
        if hasattr(params, 'set_str'):
            params.set_str(key, value)
        elif hasattr(params, 'set_param'):
            params.set_param(key, value)

    def test_get_param_value(self):
        """Test retrieving config parameter value with fallback."""
        self._set_config('ai_address_autofill.test_key', 'test_value')
        val = self.service._get_param_value('ai_address_autofill.test_key')
        self.assertEqual(val, 'test_value')

        default_val = self.service._get_param_value('ai_address_autofill.non_existent', default='fallback')
        self.assertEqual(default_val, 'fallback')

    def test_get_api_key_success(self):
        """Test retrieving configured API key."""
        self._set_config(self.service.CONFIG_API_KEY, 'AIzaSyTestKey123')
        key = self.service._get_api_key()
        self.assertEqual(key, 'AIzaSyTestKey123')

    def test_get_api_key_missing_raises_user_error(self):
        """Test UserError raised when API key is missing or empty."""
        self._set_config(self.service.CONFIG_API_KEY, '')
        with self.assertRaises(UserError):
            self.service._get_api_key()

    def test_get_model_name_default_and_custom(self):
        """Test retrieving default model name and customized model name."""
        self._set_config(self.service.CONFIG_MODEL, '')
        model = self.service._get_model_name()
        self.assertEqual(model, self.service.DEFAULT_MODEL)

        self._set_config(self.service.CONFIG_MODEL, 'gemini-3.8-flash')
        model = self.service._get_model_name()
        self.assertEqual(model, 'gemini-3.8-flash')

    def test_get_client_instantiation(self):
        """Test _get_client instantiates genai.Client with key."""
        with patch('odoo.addons.ai_address_autofill.models.gemini_service.HAS_GENAI', True), \
             patch('odoo.addons.ai_address_autofill.models.gemini_service.genai.Client') as mock_client:
            client = self.service._get_client(api_key='custom_key')
            mock_client.assert_called_once_with(api_key='custom_key')
            self.assertIsNotNone(client)

    def test_get_client_missing_sdk_raises_user_error(self):
        """Test _get_client raises UserError when HAS_GENAI is False."""
        with patch('odoo.addons.ai_address_autofill.models.gemini_service.HAS_GENAI', False):
            with self.assertRaises(UserError):
                self.service._get_client()

    def test_test_connection_success(self):
        """Test test_connection returns success on valid response."""
        mock_response = MagicMock()
        mock_response.text = 'Pong'
        mock_response.candidates = ['test_candidate']

        with patch.object(type(self.service), '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            success, msg = self.service.test_connection(api_key='valid_key', model_name='gemini-3.5-flash')
            self.assertTrue(success)
            self.assertIn("Connection successful", msg)

    def test_test_connection_empty_response(self):
        """Test test_connection when response has no text or candidates."""
        mock_response = MagicMock()
        mock_response.text = None
        mock_response.candidates = []

        with patch.object(type(self.service), '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            success, msg = self.service.test_connection(api_key='valid_key')
            self.assertTrue(success)
            self.assertIn("Google Gemini responded", msg)

    def test_test_connection_failure(self):
        """Test test_connection returns failure when API call fails."""
        with patch.object(type(self.service), '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = Exception("Connection refused")
            mock_get_client.return_value = mock_client

            success, msg = self.service.test_connection(api_key='test_key')
            self.assertFalse(success)
            self.assertTrue(len(msg) > 0)

    def test_extract_address_empty_input_raises_user_error(self):
        """Test UserError raised on empty or whitespace input."""
        with self.assertRaises(UserError):
            self.service.extract_address("")
        with self.assertRaises(UserError):
            self.service.extract_address("   \n  ")

    def test_extract_address_success(self):
        """Test extract_address parses unstructured address successfully."""
        parsed_data = {
            'street': '1600 Amphitheatre Pkwy',
            'street2': 'Building 40',
            'city': 'Mountain View',
            'state': 'CA',
            'zip': '94043',
            'country': 'United States',
        }
        mock_response = MagicMock()
        mock_response.parsed = parsed_data
        mock_response.text = None

        with patch.object(type(self.service), '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = self.service.extract_address("1600 Amphitheatre Pkwy, Mountain View, CA 94043")
            self.assertEqual(result['street'], '1600 Amphitheatre Pkwy')
            self.assertEqual(result['street2'], 'Building 40')
            self.assertEqual(result['city'], 'Mountain View')
            self.assertEqual(result['state'], 'CA')
            self.assertEqual(result['zip'], '94043')
            self.assertEqual(result['country'], 'United States')

    def test_extract_address_api_error_handling(self):
        """Test extract_address handles API exceptions and raises UserError."""
        with patch.object(type(self.service), '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = Exception("API rate limited")
            mock_get_client.return_value = mock_client

            with self.assertRaises(UserError):
                self.service.extract_address("Some address to extract")

    def test_parse_extraction_response_formats(self):
        """Test _parse_extraction_response with model_dump, dict, json text, and sanitized nulls."""
        # 1. Pydantic-like object with model_dump()
        mock_pydantic = MagicMock()
        mock_pydantic.model_dump.return_value = {
            'street': 'Main Street 1',
            'street2': 'none',
            'city': 'Metropolis',
            'state': 'null',
            'zip': '12345',
            'country': 'US',
        }
        resp1 = MagicMock()
        resp1.parsed = mock_pydantic
        res1 = self.service._parse_extraction_response(resp1)
        self.assertEqual(res1['street'], 'Main Street 1')
        self.assertFalse(res1['street2'])  # 'none' sanitized to False
        self.assertEqual(res1['city'], 'Metropolis')
        self.assertFalse(res1['state'])    # 'null' sanitized to False
        self.assertEqual(res1['zip'], '12345')
        self.assertEqual(res1['country'], 'US')

        # 2. JSON text fallback
        resp2 = MagicMock()
        resp2.parsed = None
        resp2.text = '{"street": "42 Wallaby Way", "city": "Sydney", "country": "Australia"}'
        res2 = self.service._parse_extraction_response(resp2)
        self.assertEqual(res2['street'], '42 Wallaby Way')
        self.assertEqual(res2['city'], 'Sydney')
        self.assertEqual(res2['country'], 'Australia')
        self.assertFalse(res2['street2'])

        # 3. Invalid JSON text fallback
        resp3 = MagicMock()
        resp3.parsed = None
        resp3.text = 'Invalid JSON Content'
        res3 = self.service._parse_extraction_response(resp3)
        self.assertFalse(res3['street'])
        self.assertFalse(res3['city'])

    def test_handle_gemini_exception_variations(self):
        """Test _handle_gemini_exception formatting various error types."""
        # Timeout
        msg_timeout = self.service._handle_gemini_exception(Exception("Connection timeout"))
        self.assertIn("timed out", msg_timeout)

        # Network / connection
        msg_conn = self.service._handle_gemini_exception(Exception("Network unreachable"))
        self.assertIn("Unable to connect", msg_conn)

        # Generic
        msg_gen = self.service._handle_gemini_exception(Exception("Unexpected failure"))
        self.assertIn("Unexpected failure", msg_gen)

    def test_handle_gemini_api_error_codes(self):
        """Test _handle_gemini_exception with various APIError HTTP status codes."""
        from google.genai import errors

        # 400 / Invalid API Key
        err_400 = errors.APIError(400, 'API_KEY_INVALID')
        msg_400 = self.service._handle_gemini_exception(err_400)
        self.assertIn("Invalid Google Gemini API key", msg_400)

        # 429 / Quota
        err_429 = errors.APIError(429, 'RESOURCE_EXHAUSTED')
        msg_429 = self.service._handle_gemini_exception(err_429)
        self.assertIn("quota exceeded", msg_429)

        # 500 / Server Error
        err_500 = errors.APIError(500, 'Internal Server Error')
        msg_500 = self.service._handle_gemini_exception(err_500)
        self.assertIn("temporarily unavailable", msg_500)

        # Other APIError
        err_other = errors.APIError(404, 'Model Not Found')
        msg_other = self.service._handle_gemini_exception(err_other)
        self.assertIn("Google Gemini API error", msg_other)


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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    """Test suite for Pivot AI Summary settings configuration."""

    def setUp(self):
        super(TestResConfigSettings, self).setUp()
        self.Settings = self.env['res.config.settings']
        self.icp = self.env['ir.config_parameter'].sudo()

    def test_default_config_parameters(self):
        """Test reading default values from config settings."""
        settings = self.Settings.create({})
        self.assertFalse(settings.enable_pivot_ai_summary)
        self.assertFalse(settings.api_key)

    def test_set_and_get_config_parameters(self):
        """Test setting and retrieving configuration parameters."""
        self.icp.set_param('pivot_ai_summary.enable', 'True')
        self.icp.set_param('pivot_ai_summary.system', 'gemini')
        self.icp.set_param('pivot_ai_summary.api_key', 'test_secret_key')
        self.icp.set_param('pivot_ai_summary.gemini_model', 'gemini-2.0-flash')
        self.icp.set_param('pivot_ai_summary.openai_model', 'gpt-4o-mini')

        settings = self.Settings.create({})
        self.assertTrue(settings.enable_pivot_ai_summary)
        self.assertEqual(settings.generative_ai_systems, 'gemini')
        self.assertEqual(settings.api_key, 'test_secret_key')
        self.assertEqual(settings.gemini_model_id, 'gemini-2.0-flash')
        self.assertEqual(settings.model_id, 'gpt-4o-mini')

    def test_get_openrouter_models_without_api_key(self):
        """Test _get_openrouter_models returns fallback option when no API key is provided."""
        self.icp.set_param('pivot_ai_summary.api_key', False)
        settings = self.Settings.create({'api_key': False})
        models_list = settings._get_openrouter_models()
        self.assertEqual(models_list, [('none', 'Please enter API Key and click Save')])

    @patch('requests.get')
    def test_get_openrouter_models_success(self, mock_get):
        """Test _get_openrouter_models returns sorted models when API request succeeds."""
        self.icp.set_param('pivot_ai_summary.api_key', 'valid_key')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'openai/gpt-4o', 'name': 'GPT-4o'},
                {'id': 'meta-llama/llama-3.1-8b-instruct:free', 'name': 'Llama 3.1 8B (free)'},
            ]
        }
        mock_get.return_value = mock_response

        settings = self.Settings.create({'api_key': 'valid_key'})
        models_list = settings._get_openrouter_models()

        self.assertEqual(len(models_list), 2)
        # Verify free model comes first according to sort key
        self.assertEqual(models_list[0][0], 'meta-llama/llama-3.1-8b-instruct:free')
        self.assertEqual(models_list[1][0], 'openai/gpt-4o')

    @patch('requests.get')
    def test_get_openrouter_models_http_error(self, mock_get):
        """Test _get_openrouter_models handles non-200 HTTP response codes."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        settings = self.Settings.create({'api_key': 'invalid_key'})
        models_list = settings._get_openrouter_models()
        self.assertEqual(models_list, [('none', 'API Error 401')])

    @patch('requests.get')
    def test_get_openrouter_models_exception(self, mock_get):
        """Test _get_openrouter_models handles connection exceptions gracefully."""
        mock_get.side_effect = Exception("Connection Timeout")

        settings = self.Settings.create({'api_key': 'some_key'})
        models_list = settings._get_openrouter_models()
        self.assertEqual(models_list, [('none', 'Connection Error')])

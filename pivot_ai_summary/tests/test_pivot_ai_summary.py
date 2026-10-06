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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPivotAISummary(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PivotSummary = cls.env['pivot.ai.summary']
        cls.ConfigParameter = cls.env['ir.config_parameter'].sudo()

    def setUp(self):
        super().setUp()
        # Clean config parameters before each test
        self.ConfigParameter.set_param('pivot_ai_summary.enable', False)
        self.ConfigParameter.set_param('pivot_ai_summary.system', False)
        self.ConfigParameter.set_param('pivot_ai_summary.api_key', False)
        self.ConfigParameter.set_param('pivot_ai_summary.gemini_model', False)
        self.ConfigParameter.set_param('pivot_ai_summary.openai_model', False)
        self.ConfigParameter.set_param('pivot_ai_summary.openrouter_model', False)

    def test_01_is_ai_enabled(self):
        """Test is_ai_enabled method under various configuration states."""
        # Case: Parameter is not set
        self.assertFalse(self.PivotSummary.is_ai_enabled())

        # Case: Parameter set to 'True' string
        self.ConfigParameter.set_param('pivot_ai_summary.enable', 'True')
        self.assertTrue(self.PivotSummary.is_ai_enabled())

        # Case: Parameter set to '1' string
        self.ConfigParameter.set_param('pivot_ai_summary.enable', '1')
        self.assertTrue(self.PivotSummary.is_ai_enabled())

        # Case: Parameter set to 'False' string
        self.ConfigParameter.set_param('pivot_ai_summary.enable', 'False')
        self.assertFalse(self.PivotSummary.is_ai_enabled())

    def test_02_get_openrouter_models_no_key(self):
        """Test _get_openrouter_models when API key is missing."""
        config = self.env['res.config.settings'].create({})
        res = config._get_openrouter_models()
        self.assertEqual(res, [('none', 'Please enter API Key and click Save')])

    @patch('odoo.addons.pivot_ai_summary.models.res_config_settings.requests.get')
    def test_03_get_openrouter_models_success(self, mock_get):
        """Test _get_openrouter_models with successful API response and correct sorting."""
        config = self.env['res.config.settings'].create({'api_key': 'test_key'})

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'model_paid', 'name': 'Paid Model'},
                {'id': 'model_free', 'name': 'Llama Free Model'},
            ]
        }
        mock_get.return_value = mock_response

        res = config._get_openrouter_models()
        # Free models should come first
        self.assertEqual(res, [
            ('model_free', 'Llama Free Model'),
            ('model_paid', 'Paid Model')
        ])

    @patch('odoo.addons.pivot_ai_summary.models.res_config_settings.requests.get')
    def test_04_get_openrouter_models_error(self, mock_get):
        """Test _get_openrouter_models with API error response status."""
        config = self.env['res.config.settings'].create({'api_key': 'test_key'})

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        res = config._get_openrouter_models()
        self.assertEqual(res, [('none', 'API Error 401')])

    @patch('odoo.addons.pivot_ai_summary.models.res_config_settings.requests.get')
    def test_05_get_openrouter_models_exception(self, mock_get):
        """Test _get_openrouter_models handling requests exception."""
        config = self.env['res.config.settings'].create({'api_key': 'test_key'})
        mock_get.side_effect = Exception("Connection Timeout")

        res = config._get_openrouter_models()
        self.assertEqual(res, [('none', 'Connection Error')])

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.iap_tools.iap_jsonrpc')
    def test_06_generate_summary_odoo_success(self, mock_jsonrpc):
        """Test summary generation using Odoo AI system (IAP)."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'odoo')
        self.ConfigParameter.set_param('database.uuid', 'test-db-uuid')

        mock_jsonrpc.return_value = {
            'status': 'success',
            'content': 'This is Odoo AI analysis summary.'
        }

        pivot_data = "Sales Pivot Table Data"
        history = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'ai', 'content': 'Hi there'}
        ]

        summary = self.PivotSummary.generate_summary(pivot_data, history)
        self.assertEqual(summary, 'This is Odoo AI analysis summary.')

        mock_jsonrpc.assert_called_once_with(
            "https://olg.api.odoo.com/api/olg/1/chat",
            params={
                'prompt': "You are a business analyst. Use this Odoo pivot table data:\n\nSales Pivot Table Data",
                'conversation_history': [
                    {'role': 'user', 'content': 'Hello'},
                    {'role': 'assistant', 'content': 'Hi there'}
                ],
                'database_id': 'test-db-uuid',
            },
            timeout=30
        )

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.iap_tools.iap_jsonrpc')
    def test_07_generate_summary_odoo_limit_reached(self, mock_jsonrpc):
        """Test summary generation using Odoo AI system when limit is reached."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'odoo')
        mock_jsonrpc.return_value = {
            'status': 'limit_call_reached'
        }

        summary = self.PivotSummary.generate_summary("Data")
        self.assertIn("reached the maximum number of requests", summary)

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.iap_tools.iap_jsonrpc')
    def test_08_generate_summary_odoo_error(self, mock_jsonrpc):
        """Test summary generation using Odoo AI system returning generic status error."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'odoo')
        mock_jsonrpc.return_value = {
            'status': 'failed_authorization'
        }

        summary = self.PivotSummary.generate_summary("Data")
        self.assertEqual(summary, "Odoo AI Error: failed_authorization")

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.iap_tools.iap_jsonrpc')
    def test_09_generate_summary_odoo_exception(self, mock_jsonrpc):
        """Test summary generation using Odoo AI system raising exception."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'odoo')
        mock_jsonrpc.side_effect = Exception("IAP Service Down")

        summary = self.PivotSummary.generate_summary("Data")
        self.assertEqual(summary, "Odoo AI Connection Error: IAP Service Down")

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.requests.post')
    def test_10_generate_summary_gemini_success(self, mock_post):
        """Test Gemini system success case with history formatting."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'gemini')
        self.ConfigParameter.set_param('pivot_ai_summary.api_key', 'gemini_key')
        self.ConfigParameter.set_param('pivot_ai_summary.gemini_model', 'gemini-2.0-flash')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {'text': 'Gemini Summary content.'}
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        history = [
            {'role': 'user', 'content': 'What is this data?'},
            {'role': 'ai', 'content': 'This is product sales.'}
        ]

        summary = self.PivotSummary.generate_summary("Sales Data", history)
        self.assertEqual(summary, 'Gemini Summary content.')

        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_args[0], "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=gemini_key")
        self.assertEqual(called_kwargs['json']['contents'][0]['role'], 'user')
        self.assertIn("You are a business analyst", called_kwargs['json']['contents'][0]['parts'][0]['text'])

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.requests.post')
    def test_11_generate_summary_gemini_error(self, mock_post):
        """Test Gemini system error case with custom error response."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'gemini')
        self.ConfigParameter.set_param('pivot_ai_summary.api_key', 'gemini_key')

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': {'message': 'API Key not valid'}
        }
        mock_post.return_value = mock_response

        summary = self.PivotSummary.generate_summary("Data")
        self.assertEqual(summary, "Gemini Error (400): API Key not valid")

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.requests.post')
    def test_12_generate_summary_gemini_exception(self, mock_post):
        """Test Gemini system exception handling."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'gemini')
        mock_post.side_effect = Exception("Timeout")

        summary = self.PivotSummary.generate_summary("Data")
        self.assertEqual(summary, "Gemini Connection Error: Timeout")

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.requests.post')
    def test_13_generate_summary_openai_success(self, mock_post):
        """Test OpenAI system success case."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'openai')
        self.ConfigParameter.set_param('pivot_ai_summary.api_key', 'openai_key')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': 'OpenAI Summary content.'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        summary = self.PivotSummary.generate_summary("Data")
        self.assertEqual(summary, 'OpenAI Summary content.')

        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_args[0], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(called_kwargs['headers']['Authorization'], 'Bearer openai_key')

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.requests.post')
    def test_14_generate_summary_openrouter_success(self, mock_post):
        """Test OpenRouter system success case."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'openrouter')
        self.ConfigParameter.set_param('pivot_ai_summary.api_key', 'openrouter_key')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {
                    'message': {
                        'content': 'OpenRouter Summary content.'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        summary = self.PivotSummary.generate_summary("Data")
        self.assertEqual(summary, 'OpenRouter Summary content.')

        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_args[0], "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(called_kwargs['headers']['Authorization'], 'Bearer openrouter_key')

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.requests.post')
    def test_15_generate_summary_openai_error(self, mock_post):
        """Test OpenAI/OpenRouter system error handling."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'openai')
        self.ConfigParameter.set_param('pivot_ai_summary.api_key', 'openai_key')

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            'error': {'message': 'Rate limit exceeded'}
        }
        mock_post.return_value = mock_response

        summary = self.PivotSummary.generate_summary("Data")
        self.assertEqual(summary, "Error (429): Rate limit exceeded")

    @patch('odoo.addons.pivot_ai_summary.models.ai_service.requests.post')
    def test_16_generate_summary_openai_exception(self, mock_post):
        """Test OpenAI/OpenRouter system exception handling."""
        self.ConfigParameter.set_param('pivot_ai_summary.system', 'openai')
        mock_post.side_effect = Exception("DNS Resolution Fail")

        summary = self.PivotSummary.generate_summary("Data")
        self.assertEqual(summary, "Connection Error: DNS Resolution Fail")

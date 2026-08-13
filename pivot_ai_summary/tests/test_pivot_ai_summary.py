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


class TestPivotAISummary(TransactionCase):
    """Test suite for Pivot AI Summary service (pivot.ai.summary model)."""

    def setUp(self):
        super(TestPivotAISummary, self).setUp()
        self.PivotAISummary = self.env['pivot.ai.summary']
        self.icp = self.env['ir.config_parameter'].sudo()
        self.sample_pivot_data = "Sales: $10,000 | Region: North America"

    def test_is_ai_enabled(self):
        """Test is_ai_enabled returns True when param is set to True, 1 or 'True'."""
        self.icp.set_param('pivot_ai_summary.enable', 'True')
        self.assertTrue(self.PivotAISummary.is_ai_enabled())

        self.icp.set_param('pivot_ai_summary.enable', '1')
        self.assertTrue(self.PivotAISummary.is_ai_enabled())

        self.icp.set_param('pivot_ai_summary.enable', 'False')
        self.assertFalse(self.PivotAISummary.is_ai_enabled())

    # ---------------------------------------------------------
    # Odoo AI (OLG / IAP) Tests
    # ---------------------------------------------------------
    @patch('odoo.addons.iap.tools.iap_tools.iap_jsonrpc')
    def test_generate_summary_odoo_success(self, mock_jsonrpc):
        """Test summary generation using Odoo OLG system when API returns success."""
        self.icp.set_param('pivot_ai_summary.system', 'odoo')
        mock_jsonrpc.return_value = {
            'status': 'success',
            'content': 'Sales in North America performed exceptionally well.'
        }

        result = self.PivotAISummary.generate_summary(self.sample_pivot_data)
        self.assertEqual(result, 'Sales in North America performed exceptionally well.')

    @patch('odoo.addons.iap.tools.iap_tools.iap_jsonrpc')
    def test_generate_summary_odoo_limit_reached(self, mock_jsonrpc):
        """Test Odoo OLG rate limit response."""
        self.icp.set_param('pivot_ai_summary.system', 'odoo')
        mock_jsonrpc.return_value = {'status': 'limit_call_reached'}

        result = self.PivotAISummary.generate_summary(self.sample_pivot_data)
        self.assertIn("reached the maximum number of requests", result)

    @patch('odoo.addons.iap.tools.iap_tools.iap_jsonrpc')
    def test_generate_summary_odoo_error(self, mock_jsonrpc):
        """Test Odoo OLG error response."""
        self.icp.set_param('pivot_ai_summary.system', 'odoo')
        mock_jsonrpc.return_value = {'status': 'invalid_token'}

        result = self.PivotAISummary.generate_summary(self.sample_pivot_data)
        self.assertEqual(result, "Odoo AI Error: invalid_token")

    @patch('odoo.addons.iap.tools.iap_tools.iap_jsonrpc')
    def test_generate_summary_odoo_connection_error(self, mock_jsonrpc):
        """Test Odoo OLG connection exception handling."""
        self.icp.set_param('pivot_ai_summary.system', 'odoo')
        mock_jsonrpc.side_effect = Exception("Service unavailable")

        result = self.PivotAISummary.generate_summary(self.sample_pivot_data)
        self.assertEqual(result, "Odoo AI Connection Error: Service unavailable")

    # ---------------------------------------------------------
    # Google Gemini Tests
    # ---------------------------------------------------------
    @patch('requests.post')
    def test_generate_summary_gemini_success(self, mock_post):
        """Test summary generation using Google Gemini system."""
        self.icp.set_param('pivot_ai_summary.system', 'gemini')
        self.icp.set_param('pivot_ai_summary.api_key', 'gemini_key_123')
        self.icp.set_param('pivot_ai_summary.gemini_model', 'gemini-2.0-flash')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Gemini summary analysis.'}]}}]
        }
        mock_post.return_value = mock_response

        history = [{'role': 'user', 'content': 'Hi'}, {'role': 'ai', 'content': 'Hello'}]
        result = self.PivotAISummary.generate_summary(self.sample_pivot_data, history=history)

        self.assertEqual(result, 'Gemini summary analysis.')
        self.assertTrue(mock_post.called)

    @patch('requests.post')
    def test_generate_summary_gemini_error(self, mock_post):
        """Test Gemini API error response handling."""
        self.icp.set_param('pivot_ai_summary.system', 'gemini')
        self.icp.set_param('pivot_ai_summary.api_key', 'invalid_key')

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': {'message': 'API key not valid'}}
        mock_post.return_value = mock_response

        result = self.PivotAISummary.generate_summary(self.sample_pivot_data)
        self.assertEqual(result, "Gemini Error (400): API key not valid")

    @patch('requests.post')
    def test_generate_summary_gemini_connection_error(self, mock_post):
        """Test Gemini network connection exception."""
        self.icp.set_param('pivot_ai_summary.system', 'gemini')
        mock_post.side_effect = Exception("Connection Reset")

        result = self.PivotAISummary.generate_summary(self.sample_pivot_data)
        self.assertEqual(result, "Gemini Connection Error: Connection Reset")

    # ---------------------------------------------------------
    # OpenAI & OpenRouter Tests
    # ---------------------------------------------------------
    @patch('requests.post')
    def test_generate_summary_openai_success(self, mock_post):
        """Test summary generation using OpenAI system."""
        self.icp.set_param('pivot_ai_summary.system', 'openai')
        self.icp.set_param('pivot_ai_summary.api_key', 'sk-test-key')
        self.icp.set_param('pivot_ai_summary.openai_model', 'gpt-4o-mini')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'OpenAI analysis result.'}}]
        }
        mock_post.return_value = mock_response

        result = self.PivotAISummary.generate_summary(self.sample_pivot_data)
        self.assertEqual(result, 'OpenAI analysis result.')

    @patch('requests.post')
    def test_generate_summary_openrouter_success(self, mock_post):
        """Test summary generation using OpenRouter system."""
        self.icp.set_param('pivot_ai_summary.system', 'openrouter')
        self.icp.set_param('pivot_ai_summary.api_key', 'or-key')

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'OpenRouter analysis result.'}}]
        }
        mock_post.return_value = mock_response

        result = self.PivotAISummary.generate_summary(self.sample_pivot_data)
        self.assertEqual(result, 'OpenRouter analysis result.')

    @patch('requests.post')
    def test_generate_summary_openai_connection_error(self, mock_post):
        """Test OpenAI/OpenRouter network connection exception."""
        self.icp.set_param('pivot_ai_summary.system', 'openai')
        mock_post.side_effect = Exception("Read Timeout")

        result = self.PivotAISummary.generate_summary(self.sample_pivot_data)
        self.assertEqual(result, "Connection Error: Read Timeout")

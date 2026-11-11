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
"""Tests for Pivot AI Summary configuration settings."""
from unittest.mock import Mock, patch

from odoo.tests.common import TransactionCase, tagged



@tagged('post_install', '-at_install')
class TestPivotAISummarySettings(TransactionCase):
    """Verify settings persistence and OpenRouter model loading."""

    def test_settings_are_saved_to_config_parameters(self):
        settings = self.env['res.config.settings'].create({
            'enable_pivot_ai_summary': True,
            'generative_ai_systems': 'openai',
            'api_key': 'test-api-key',
            'model_id': 'gpt-4o-mini',
        })
        settings.execute()

        parameters = self.env['ir.config_parameter'].sudo()
        self.assertEqual(parameters.get_str('pivot_ai_summary.enable'), 'True')
        self.assertEqual(parameters.get_str('pivot_ai_summary.system'), 'openai')
        self.assertEqual(parameters.get_str('pivot_ai_summary.api_key'), 'test-api-key')
        self.assertEqual(parameters.get_str('pivot_ai_summary.openai_model'), 'gpt-4o-mini')

    def test_openrouter_models_without_api_key(self):
        settings = self.env['res.config.settings'].new()
        self.assertEqual(
            settings._get_openrouter_models(),
            [('none', 'Please enter API Key and click Save')],
        )

    @patch('odoo.addons.pivot_ai_summary.models.res_config_settings.requests.get')
    def test_openrouter_models_are_sorted_with_free_first(self, get):
        response = Mock(status_code=200)
        response.json.return_value = {
            'data': [
                {'id': 'provider/paid', 'name': 'Paid model'},
                {'id': 'provider/free', 'name': 'Free model'},
            ],
        }
        get.return_value = response
        settings = self.env['res.config.settings'].new({'api_key': 'test-key'})

        models = settings._get_openrouter_models()

        self.assertEqual(models, [
            ('provider/free', 'Free model'),
            ('provider/paid', 'Paid model'),
        ])
        get.assert_called_once()
        self.assertEqual(get.call_args.kwargs['headers']['Authorization'], 'Bearer test-key')

    @patch('odoo.addons.pivot_ai_summary.models.res_config_settings.requests.get')
    def test_openrouter_api_and_connection_errors(self, get):
        settings = self.env['res.config.settings'].new({'api_key': 'test-key'})

        response = Mock(status_code=503)
        get.return_value = response
        self.assertEqual(settings._get_openrouter_models(), [('none', 'API Error 503')])

        get.side_effect = OSError('network unavailable')
        self.assertEqual(settings._get_openrouter_models(), [('none', 'Connection Error')])

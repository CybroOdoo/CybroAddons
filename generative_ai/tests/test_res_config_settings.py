# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import MagicMock, patch

import requests

from odoo.tests import TransactionCase, tagged

REQUESTS_GET = ('odoo.addons.generative_ai.models.res_config_settings'
                '.requests.get')


def _response(status_code=200, data=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {'data': data if data is not None else []}
    return response


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Tests for the AI provider configuration."""

    def setUp(self):
        super().setUp()
        self.icp = self.env['ir.config_parameter'].sudo()
        self.settings = self.env['res.config.settings'].create({})

    def test_default_get_max_token(self):
        values = self.env['res.config.settings'].default_get(['max_token'])
        self.assertEqual(values['max_token'], '4096')

    def test_get_values_defaults(self):
        values = self.settings.get_values()
        self.assertEqual(values['max_token'], '4096')
        self.assertFalse(values['generative_ai_systems'])

    def test_onchange_clears_models_without_key(self):
        self.settings.generative_ai_systems = 'openai'
        self.settings.api_key = False
        self.settings.model_id = 'gpt-4o'
        self.settings._onchange_generative_ai_systems()
        self.assertFalse(self.settings.model_id)

    def test_model_selection_without_configuration(self):
        self.assertEqual(self.settings._get_model_selection(),
                         [('none', 'No Models Available')])

    def test_model_selection_openai_has_no_remote_call(self):
        self.settings.generative_ai_systems = 'openai'
        self.settings.api_key = 'key'
        with patch(REQUESTS_GET) as mocked:
            result = self.settings._get_model_selection()
        mocked.assert_not_called()
        self.assertEqual(result, [('none', 'No Models Available')])

    def test_model_selection_openrouter_success(self):
        self.settings.generative_ai_systems = 'openrouter'
        self.settings.api_key = 'key'
        data = [{'id': 'vendor/model-a', 'name': 'Model A'}]
        with patch(REQUESTS_GET, return_value=_response(200, data)):
            result = self.settings._get_model_selection()
        self.assertEqual(result, [('vendor/model-a', 'Model A')])

    def test_model_selection_openrouter_empty(self):
        self.settings.generative_ai_systems = 'openrouter'
        self.settings.api_key = 'key'
        with patch(REQUESTS_GET, return_value=_response(200, [])):
            result = self.settings._get_model_selection()
        self.assertEqual(result, [('none', 'No Models Available')])

    def test_model_selection_openrouter_api_error(self):
        self.settings.generative_ai_systems = 'openrouter'
        self.settings.api_key = 'key'
        with patch(REQUESTS_GET, return_value=_response(401)):
            result = self.settings._get_model_selection()
        self.assertEqual(result, [('none', 'API Error: 401')])

    def test_model_selection_connection_error(self):
        self.settings.generative_ai_systems = 'openrouter'
        self.settings.api_key = 'key'
        with patch(REQUESTS_GET,
                   side_effect=requests.exceptions.ConnectionError()):
            result = self.settings._get_model_selection()
        self.assertEqual(result, [('none', 'Connection Error')])

    def test_model_selection_unexpected_error(self):
        self.settings.generative_ai_systems = 'openrouter'
        self.settings.api_key = 'key'
        with patch(REQUESTS_GET, side_effect=ValueError('boom')):
            result = self.settings._get_model_selection()
        self.assertEqual(result, [('none', 'Error Loading Models')])

    def test_set_values_openai(self):
        settings = self.env['res.config.settings'].create({
            'generative_ai_systems': 'openai',
            'api_key': 'secret',
            'model_id': 'gpt-4o',
            'max_token': '1000',
        })
        settings.set_values()
        self.assertEqual(self.icp.get_str('generative_ai_systems'), 'openai')
        self.assertEqual(self.icp.get_str('api_key'), 'secret')
        self.assertEqual(self.icp.get_str('model_id'), 'gpt-4o')
        self.assertEqual(self.icp.get_str('max_token'), '1000')

    def test_set_values_openrouter_keeps_valid_model(self):
        data = [{'id': 'vendor/a', 'name': 'A'}, {'id': 'vendor/b', 'name': 'B'}]
        with patch(REQUESTS_GET, return_value=_response(200, data)):
            settings = self.env['res.config.settings'].create({
                'generative_ai_systems': 'openrouter',
                'api_key': 'secret',
                'openrouter_model_id': 'vendor/b',
            })
            settings.set_values()
        self.assertEqual(self.icp.get_str('openrouter_model_id'), 'vendor/b')

    def test_set_values_openrouter_without_models(self):
        with patch(REQUESTS_GET, return_value=_response(200, [])):
            settings = self.env['res.config.settings'].create({
                'generative_ai_systems': 'openrouter',
                'api_key': 'secret',
            })
            settings.set_values()
        self.assertFalse(self.icp.get_str('openrouter_model_id'))

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

import requests

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import PROVIDERS_PATH, AiConnectorCommon, make_response


@tagged('post_install', '-at_install', 'ai_connector_agent')
class TestProviderFetchModels(AiConnectorCommon):

    def _fetch(self, provider, response=None, side_effect=None):
        with patch('%s.requests.get' % PROVIDERS_PATH,
                   return_value=response, side_effect=side_effect) as mock_get:
            provider.action_fetch_models()
        return mock_get

    def test_openai_headers_and_models_from_data_key(self):
        provider = self._make_provider('OpenAI', 'https://api.openai.com/')
        resp = make_response(200, {'data': [
            {'id': 'fetch-gpt-1', 'object': 'model', 'owned_by': 'openai'},
            {'id': 'fetch-gpt-2', 'object': 'model', 'owned_by': 'openai'},
        ]})
        mock_get = self._fetch(provider, resp)
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], 'https://api.openai.com/v1/models')
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer key')
        self.assertEqual(kwargs['params'], {})
        self.assertEqual(
            sorted(provider.ai_model_ids.mapped('model_ref_id')),
            ['fetch-gpt-1', 'fetch-gpt-2'])
        created = provider.ai_model_ids.filtered(
            lambda m: m.model_ref_id == 'fetch-gpt-1')
        self.assertEqual(created.owned_by, 'openai')
        self.assertEqual(created.display_label, 'model')

    def test_chatgpt_name_uses_bearer(self):
        provider = self._make_provider('My ChatGPT', 'https://example.com')
        resp = make_response(200, {'data': [{'id': 'x-chat-1'}]})
        mock_get = self._fetch(provider, resp)
        self.assertIn('Authorization', mock_get.call_args.kwargs['headers'])

    def test_anthropic_headers(self):
        provider = self._make_provider('Anthropic', 'https://api.anthropic.com')
        resp = make_response(200, {'data': [{'id': 'fetch-claude-1'}]})
        mock_get = self._fetch(provider, resp)
        headers = mock_get.call_args.kwargs['headers']
        self.assertEqual(headers['x-api-key'], 'key')
        self.assertEqual(headers['anthropic-version'], '2023-06-01')

    def test_gemini_uses_key_param_and_models_key(self):
        provider = self._make_provider(
            'Gemini', 'https://generativelanguage.googleapis.com')
        provider.fetch_model_endpoint = 'v1beta/models'
        resp = make_response(200, {'models': [
            {'name': 'models/fetch-gemini-1', 'displayName': 'Gemini One',
             'version': '001'},
        ]})
        mock_get = self._fetch(provider, resp)
        args, kwargs = mock_get.call_args
        self.assertEqual(
            args[0], 'https://generativelanguage.googleapis.com/v1beta/models')
        self.assertEqual(kwargs['params'], {'key': 'key'})
        self.assertEqual(kwargs['headers'], {})
        model = provider.ai_model_ids
        self.assertEqual(model.model_ref_id, 'fetch-gemini-1')
        self.assertEqual(model.display_label, 'Gemini One')
        self.assertEqual(model.version, '001')

    def test_existing_model_is_reused(self):
        existing = self.Model.create({'model_ref_id': 'shared-model'})
        provider = self._make_provider('OpenAI', 'https://api.openai.com')
        resp = make_response(200, {'data': [{'id': 'shared-model'}]})
        self._fetch(provider, resp)
        self.assertEqual(provider.ai_model_ids, existing)
        self.assertEqual(
            self.Model.search_count([('model_ref_id', '=', 'shared-model')]), 1)

    def test_records_without_id_are_skipped(self):
        provider = self._make_provider('OpenAI', 'https://api.openai.com')
        resp = make_response(200, {'data': [{'object': 'model'}, {'id': 'ok-1'}]})
        self._fetch(provider, resp)
        self.assertEqual(provider.ai_model_ids.mapped('model_ref_id'), ['ok-1'])

    def test_fetch_replaces_previous_models(self):
        provider = self._make_provider(
            'OpenAI', 'https://api.openai.com', self.model_a)
        resp = make_response(200, {'data': [{'id': 'brand-new'}]})
        self._fetch(provider, resp)
        self.assertEqual(provider.ai_model_ids.mapped('model_ref_id'), ['brand-new'])

    def test_non_200_raises(self):
        provider = self._make_provider('OpenAI', 'https://api.openai.com')
        with self.assertRaisesRegex(UserError, '401'):
            self._fetch(provider, make_response(401, text='unauthorized'))

    def test_invalid_json_raises(self):
        provider = self._make_provider('OpenAI', 'https://api.openai.com')
        with self.assertRaisesRegex(UserError, 'Invalid JSON'):
            self._fetch(provider, make_response(200, json_raises=True))

    def test_non_dict_payload_raises(self):
        provider = self._make_provider('OpenAI', 'https://api.openai.com')
        with self.assertRaisesRegex(UserError, 'not a dict'):
            self._fetch(provider, make_response(200, json_data=['a', 'b']))

    def test_missing_models_list_raises(self):
        provider = self._make_provider('OpenAI', 'https://api.openai.com')
        with self.assertRaisesRegex(UserError, 'Could not find a models list'):
            self._fetch(provider, make_response(200, {'something': 1}))

    def test_data_not_a_list_raises(self):
        provider = self._make_provider('OpenAI', 'https://api.openai.com')
        with self.assertRaisesRegex(UserError, 'Could not find a models list'):
            self._fetch(provider, make_response(200, {'data': 'nope'}))

    def test_empty_models_list_raises(self):
        provider = self._make_provider('OpenAI', 'https://api.openai.com')
        with self.assertRaisesRegex(UserError, 'No models returned'):
            self._fetch(provider, make_response(200, {'models': []}))

    def test_request_exception_raises_user_error(self):
        provider = self._make_provider('OpenAI', 'https://api.openai.com')
        with self.assertRaisesRegex(UserError, 'Request failed'):
            self._fetch(
                provider, side_effect=requests.exceptions.ConnectionError('boom'))

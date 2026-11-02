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

from odoo.tests import tagged

from odoo.addons.ai_connector_agent.controllers.ai_connector_agent import (
    AiChatController,
)

from .common import CONTROLLER_PATH, AiConnectorCommon, make_response


@tagged('post_install', '-at_install', 'ai_connector_agent')
class TestControllerAiCalls(AiConnectorCommon):

    def setUp(self):
        super().setUp()
        self.controller = AiChatController()

    def _post(self, response=None, side_effect=None):
        return patch(
            '%s.requests.post' % CONTROLLER_PATH,
            return_value=response, side_effect=side_effect)

    def _session_with_history(self, provider, model):
        session = self._make_session(provider, model)
        self._add_message(session, 'user', 'first question')
        self._add_message(session, 'ai', 'first answer')
        current = self._add_message(session, 'user', 'current question')
        return session, current

    # ---- _get_ai_response dispatch ---------------------------------------
    def test_dispatch_openai(self):
        with patch.object(
                AiChatController, '_call_openai_api', return_value='o') as m:
            res = self.controller._get_ai_response(
                'hi', self.provider, self.model_a, self._make_session())
        self.assertEqual(res, 'o')
        m.assert_called_once()

    def test_dispatch_anthropic_by_name_and_claude(self):
        for name in ('Anthropic', 'My Claude'):
            prov = self._make_provider(name, 'https://example.com')
            with patch.object(
                    AiChatController, '_call_anthropic_api', return_value='a'):
                res = self.controller._get_ai_response(
                    'hi', prov, self.model_a, self._make_session(prov))
            self.assertEqual(res, 'a')

    def test_dispatch_gemini_by_name_google_and_url(self):
        cases = (('Gemini', 'https://x.com'), ('Google AI', 'https://x.com'),
                 ('Custom', 'https://generativelanguage.googleapis.com'))
        for name, url in cases:
            prov = self._make_provider(name, url)
            with patch.object(
                    AiChatController, '_call_gemini_api', return_value='g'):
                res = self.controller._get_ai_response(
                    'hi', prov, self.model_a, self._make_session(prov))
            self.assertEqual(res, 'g')

    def test_dispatch_unknown_provider(self):
        prov = self._make_provider('Mystery', 'https://mystery.example')
        res = self.controller._get_ai_response(
            'hi', prov, self.model_a, self._make_session(prov))
        self.assertIn('Unable to determine the API type', res)
        self.assertIn('Mystery', res)

    def test_dispatch_missing_agent(self):
        res = self.controller._get_ai_response(
            'hi', self.Provider.browse(), self.model_a, self._make_session())
        self.assertEqual(res, 'Error: AI Agent not found.')

    def test_dispatch_exception(self):
        with patch.object(
                AiChatController, '_call_openai_api', side_effect=Exception('x')):
            res = self.controller._get_ai_response(
                'hi', self.provider, self.model_a, self._make_session())
        self.assertIn('trouble processing your request', res)

    # ---- OpenAI -----------------------------------------------------------
    def test_openai_success_payload(self):
        session, current = self._session_with_history(self.provider, self.model_a)
        with self._post(make_response(200, {
                'choices': [{'message': {'content': 'hello!'}}]})) as post:
            res = self.controller._call_openai_api(
                'current question', self.model_a, session, current)
        self.assertEqual(res, 'hello!')
        args, kwargs = post.call_args
        self.assertEqual(args[0], 'https://api.openai.com/v1/chat/completions')
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer sk-test')
        msgs = kwargs['json']['messages']
        self.assertEqual(msgs[0], {'role': 'user', 'content': 'first question'})
        self.assertEqual(msgs[1]['role'], 'assistant')
        self.assertEqual(kwargs['json']['model'], 'test-model-a')

    def test_openai_base_url_with_v1_not_duplicated(self):
        prov = self._make_provider('OpenAI', 'https://api.openai.com/v1/')
        session = self._make_session(prov)
        with self._post(make_response(200, {'choices': [{'message': {}}]})) as post:
            self.controller._call_openai_api('x', self.model_a, session)
        self.assertEqual(
            post.call_args.args[0], 'https://api.openai.com/v1/chat/completions')

    def test_openai_image_attachment(self):
        session = self._make_session()
        user_msg = self._add_message(session)
        user_msg.attachment_ids = [(6, 0, self._make_attachment().ids)]
        text_att = self._make_attachment('note.txt', self._b64('hi'))
        user_msg.attachment_ids = [(4, text_att.id)]
        with self._post(make_response(200, {'choices': [{'message': {'content': 'ok'}}]})) as post:
            self.controller._call_openai_api('x', self.model_a, session, user_msg)
        content = post.call_args.kwargs['json']['messages'][-1]['content']
        self.assertEqual([c['type'] for c in content], ['text', 'image_url'])
        self.assertTrue(content[1]['image_url']['url'].startswith('data:image/png;base64,'))

    def test_openai_empty_choices(self):
        session = self._make_session()
        with self._post(make_response(200, {'choices': []})):
            res = self.controller._call_openai_api('x', self.model_a, session)
        self.assertEqual(res, 'I received an empty response from OpenAI.')

    def test_openai_error_with_message(self):
        session = self._make_session()
        with self._post(make_response(
                400, {'error': {'message': 'bad request'}})):
            res = self.controller._call_openai_api('x', self.model_a, session)
        self.assertEqual(res, 'OpenAI API Error (400): bad request')

    def test_openai_error_without_message(self):
        session = self._make_session()
        with self._post(make_response(500, {})):
            self.assertEqual(
                self.controller._call_openai_api('x', self.model_a, session),
                'OpenAI API Error: 500')

    def test_openai_error_non_json(self):
        session = self._make_session()
        with self._post(make_response(502, json_raises=True)):
            self.assertEqual(
                self.controller._call_openai_api('x', self.model_a, session),
                'OpenAI API Error: 502')

    def test_openai_connection_failure(self):
        session = self._make_session()
        with self._post(side_effect=Exception('down')):
            self.assertEqual(
                self.controller._call_openai_api('x', self.model_a, session),
                'Failed to connect to OpenAI API.')

    # ---- Anthropic --------------------------------------------------------
    def _anthropic(self):
        prov = self._make_provider('Anthropic', 'https://api.anthropic.com/')
        return prov, self._make_session(prov)

    def test_anthropic_success_payload(self):
        prov = self._make_provider('Anthropic', 'https://api.anthropic.com/')
        session, current = self._session_with_history(prov, self.model_a)
        with self._post(make_response(200, {'content': [{'text': 'hey'}]})) as post:
            res = self.controller._call_anthropic_api(
                'current question', self.model_a, session, current)
        self.assertEqual(res, 'hey')
        args, kwargs = post.call_args
        self.assertEqual(args[0], 'https://api.anthropic.com/v1/messages')
        self.assertEqual(kwargs['headers']['x-api-key'], 'key')
        self.assertEqual(kwargs['headers']['anthropic-version'], '2023-06-01')
        self.assertEqual(kwargs['json']['max_tokens'], 4096)
        self.assertEqual(kwargs['json']['messages'][1]['role'], 'assistant')

    def test_anthropic_image_attachment(self):
        prov, session = self._anthropic()
        user_msg = self._add_message(session)
        user_msg.attachment_ids = [(6, 0, self._make_attachment().ids)]
        with self._post(make_response(200, {'content': [{'text': 'ok'}]})) as post:
            self.controller._call_anthropic_api('x', self.model_a, session, user_msg)
        content = post.call_args.kwargs['json']['messages'][-1]['content']
        self.assertEqual(content[1]['type'], 'image')
        self.assertEqual(content[1]['source']['type'], 'base64')
        self.assertEqual(content[1]['source']['media_type'], 'image/png')

    def test_anthropic_empty_content(self):
        _prov, session = self._anthropic()
        with self._post(make_response(200, {'content': []})):
            self.assertEqual(
                self.controller._call_anthropic_api('x', self.model_a, session),
                'I received an empty response from Anthropic.')

    def test_anthropic_error_variants(self):
        _prov, session = self._anthropic()
        cases = (
            (make_response(400, {'error': {'message': 'nope'}}),
             'Anthropic API Error (400): nope'),
            (make_response(500, {}), 'Anthropic API Error: 500'),
            (make_response(503, json_raises=True), 'Anthropic API Error: 503'),
        )
        for response, expected in cases:
            with self._post(response):
                self.assertEqual(
                    self.controller._call_anthropic_api('x', self.model_a, session),
                    expected)

    def test_anthropic_connection_failure(self):
        _prov, session = self._anthropic()
        with self._post(side_effect=Exception('down')):
            self.assertEqual(
                self.controller._call_anthropic_api('x', self.model_a, session),
                'Failed to connect to Anthropic API.')

    # ---- Gemini -----------------------------------------------------------
    def _gemini(self, model_ref='gemini-2.0-flash', base_url='https://generativelanguage.googleapis.com/'):
        prov = self._make_provider('Gemini', base_url)
        model = self.Model.create({'model_ref_id': model_ref})
        return prov, model, self._make_session(prov, model)

    def test_gemini_success_with_system_instruction_and_history(self):
        prov, model = self._gemini()[:2]
        session, current = self._session_with_history(prov, model)
        ok = make_response(200, {'candidates': [
            {'content': {'parts': [{'text': 'gemini reply'}]}}]})
        with self._post(ok) as post:
            res = self.controller._call_gemini_api(
                'current question', prov, model, session, current)
        self.assertEqual(res, 'gemini reply')
        args, kwargs = post.call_args
        self.assertEqual(
            args[0],
            'https://generativelanguage.googleapis.com/v1beta/models/'
            'gemini-2.0-flash:generateContent')
        self.assertEqual(kwargs['params'], {'key': 'key'})
        self.assertIn('systemInstruction', kwargs['json'])
        roles = [c['role'] for c in kwargs['json']['contents']]
        self.assertEqual(roles, ['user', 'model', 'user'])

    def test_gemini_no_system_instruction_for_old_model(self):
        prov, model, session = self._gemini(model_ref='gemini-pro')
        ok = make_response(200, {'candidates': [
            {'content': {'parts': [{'text': 't'}]}}]})
        with self._post(ok) as post:
            self.controller._call_gemini_api('x', prov, model, session)
        self.assertNotIn('systemInstruction', post.call_args.kwargs['json'])

    def test_gemini_image_attachment(self):
        prov, model, session = self._gemini()
        user_msg = self._add_message(session)
        user_msg.attachment_ids = [(6, 0, self._make_attachment().ids)]
        ok = make_response(200, {'candidates': [
            {'content': {'parts': [{'text': 't'}]}}]})
        with self._post(ok) as post:
            self.controller._call_gemini_api('x', prov, model, session, user_msg)
        parts = post.call_args.kwargs['json']['contents'][-1]['parts']
        self.assertEqual(parts[1]['inline_data']['mime_type'], 'image/png')

    def test_gemini_empty_responses(self):
        prov, model, session = self._gemini()
        for body in ({'candidates': []}, {'candidates': [{'content': {}}]}):
            with self._post(make_response(200, body)):
                self.assertEqual(
                    self.controller._call_gemini_api('x', prov, model, session),
                    'I received an empty response from Gemini.')

    def test_gemini_rate_limit_with_retry_delay(self):
        prov, model, session = self._gemini()
        body = {'error': {'details': [
            {'@type': 'type.googleapis.com/google.rpc.RetryInfo',
             'retryDelay': '27s'}]}}
        with self._post(make_response(429, body)):
            res = self.controller._call_gemini_api('x', prov, model, session)
        self.assertIn('27', res)
        self.assertIn('free-tier quota limit', res)

    def test_gemini_rate_limit_without_retry_info(self):
        prov, model, session = self._gemini()
        with self._post(make_response(429, {'error': {}})):
            res = self.controller._call_gemini_api('x', prov, model, session)
        self.assertIn('Quota exceeded', res)

    def test_gemini_rate_limit_non_json(self):
        prov, model, session = self._gemini()
        with self._post(make_response(429, json_raises=True)):
            res = self.controller._call_gemini_api('x', prov, model, session)
        self.assertIn('Quota exceeded', res)

    def test_gemini_error_variants(self):
        prov, model, session = self._gemini()
        cases = (
            (make_response(400, {'error': {'message': 'bad key'}}),
             'Gemini API Error (400): bad key'),
            (make_response(500, {}), 'Gemini API Error: 500'),
            (make_response(500, json_raises=True), 'Gemini API Error: 500'),
        )
        for response, expected in cases:
            with self._post(response):
                self.assertEqual(
                    self.controller._call_gemini_api('x', prov, model, session),
                    expected)

    def test_gemini_connection_failure(self):
        prov, model, session = self._gemini()
        with self._post(side_effect=Exception('down')):
            self.assertEqual(
                self.controller._call_gemini_api('x', prov, model, session),
                'Failed to connect to Gemini API.')

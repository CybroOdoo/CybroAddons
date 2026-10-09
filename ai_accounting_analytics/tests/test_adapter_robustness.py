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
"""Provider adapters against the irregular streams real endpoints send."""
import json
from unittest.mock import MagicMock, patch

import requests

from odoo.tests import BaseCase, tagged

from odoo.addons.ai_accounting_analytics.llm import (
    AnthropicAdapter, GeminiAdapter, LLMError, OpenAICompatAdapter, OpenRouterAdapter, ToolCall,
)
from odoo.addons.ai_accounting_analytics.llm.base import http_error

from .test_adapters import TOOLS, fake_response, run, sse

POST = 'odoo.addons.ai_accounting_analytics.llm.base.requests.post'
TRANSCRIPT = [
    {'role': 'user', 'content': 'First'},
    {'role': 'assistant', 'content': ''},          # an answer that was empty
    {'role': 'user', 'content': 'Second'},
    {'role': 'assistant', 'content': '', 'tool_calls': [
        ToolCall(id='c1', name='get_kpi_overview', arguments={})]},
    {'role': 'tool', 'results': [{'id': 'c1', 'name': 'get_kpi_overview', 'content': '{"revenue":1}'}]},
]


@tagged('-at_install', 'post_install')
class TestAdapterRobustness(BaseCase):

    def test_openai_tool_calls_without_index(self):
        """Some OpenAI-compatible endpoints omit the index of parallel calls."""
        lines = sse(
            {'choices': [{'delta': {'tool_calls': [{'id': 'a', 'function': {'name': 'get_kpi_overview',
                                                                            'arguments': '{"period":'}}]}}]},
            {'choices': [{'delta': {'tool_calls': [{'function': {'arguments': '"today"}'}}]}}]},
            {'choices': [{'delta': {'tool_calls': [{'id': 'b', 'function': {'name': 'get_cash_balances',
                                                                            'arguments': '{}'}}]}}]},
            '[DONE]')
        _payload, _texts, result, _post = run(OpenAICompatAdapter('k', 'm'), lines)
        self.assertEqual([(call.id, call.name, call.arguments) for call in result.tool_calls],
                         [('a', 'get_kpi_overview', {'period': 'today'}), ('b', 'get_cash_balances', {})])
        self.assertFalse(any(call.invalid_arguments for call in result.tool_calls))

    def test_openai_odd_arguments(self):
        for raw, expected, invalid in (('', {}, False), ('null', {}, False), ('{"a": 1', {}, True),
                                       ('"{\\"period\\": \\"today\\"}"', {'period': 'today'}, False)):
            with self.subTest(raw=raw):
                lines = sse({'choices': [{'delta': {'tool_calls': [{'index': 0, 'id': 'a', 'function': {
                    'name': 'get_kpi_overview', 'arguments': raw}}]}}]}, '[DONE]')
                _payload, _texts, result, _post = run(OpenAICompatAdapter('k', 'm'), lines)
                self.assertEqual(result.tool_calls[0].arguments, expected)
                self.assertEqual(result.tool_calls[0].invalid_arguments, invalid)

    def test_openai_truncated_stream(self):
        """No [DONE], no usage, finish_reason length: still a result."""
        lines = sse({'choices': [{'delta': {'content': 'Revenue is'}, 'finish_reason': 'length'}]})
        _payload, texts, result, _post = run(OpenAICompatAdapter('k', 'm'), lines)
        self.assertEqual(texts, ['Revenue is'])
        self.assertEqual(result.stop_reason, 'length')
        self.assertEqual(result.usage.input_tokens, 0)

    def test_sse_irregular_lines(self):
        """Comments, keep-alives, CRLF, "data:" without a space and
        non-JSON payloads are tolerated."""
        lines = [': keep-alive', '', 'data:{"choices":[{"delta":{"content":"A"}}]}\r', '\r',
                 'data: not json', '', 'event: ping', 'data: {}', '',
                 'data: {"choices":[{"delta":{"content":"B"}}]}', '', 'data: [DONE]', '']
        _payload, texts, _result, _post = run(OpenRouterAdapter('k', 'm'), lines)
        self.assertEqual(''.join(texts), 'AB')

    def test_gemini_malformed_function_call_is_retryable(self):
        lines = sse({'candidates': [{'content': {'parts': []}, 'finishReason': 'MALFORMED_FUNCTION_CALL'}]})
        with self.assertRaises(LLMError) as caught:
            run(GeminiAdapter('k', 'gemini-3.5-flash-lite'), lines)
        self.assertTrue(caught.exception.retryable)

    def test_gemini_safety_stop_gives_an_empty_result(self):
        lines = sse({'candidates': [{'finishReason': 'SAFETY'}], 'usageMetadata': {'promptTokenCount': 10}})
        _payload, texts, result, _post = run(GeminiAdapter('k', 'gemini-3.5-flash-lite'), lines)
        self.assertEqual((texts, result.tool_calls, result.stop_reason), ([], [], 'SAFETY'))

    def test_gemini_function_call_without_args(self):
        lines = sse({'candidates': [{'content': {'parts': [{'functionCall': {'name': 'get_kpi_overview'}}]}}]})
        _payload, _texts, result, _post = run(GeminiAdapter('k', 'gemini-3.5-flash-lite'), lines)
        self.assertEqual(result.tool_calls[0].arguments, {})

    def test_anthropic_max_tokens_inside_a_tool_call(self):
        lines = sse(
            ('message_start', {'type': 'message_start', 'message': {'usage': {'input_tokens': 5}}}),
            ('content_block_start', {'type': 'content_block_start', 'index': 0, 'content_block': {
                'type': 'tool_use', 'id': 't1', 'name': 'get_kpi_overview', 'input': {}}}),
            ('content_block_delta', {'type': 'content_block_delta', 'index': 0, 'delta': {
                'type': 'input_json_delta', 'partial_json': '{"period": "thi'}}),
            ('message_delta', {'type': 'message_delta', 'delta': {'stop_reason': 'max_tokens'},
                               'usage': {'output_tokens': 1024}}),
        )
        _payload, _texts, result, _post = run(AnthropicAdapter('k', 'claude-sonnet-5-5'), lines)
        self.assertTrue(result.tool_calls[0].invalid_arguments)
        self.assertEqual(result.stop_reason, 'max_tokens')

    def test_empty_assistant_turns_are_never_sent(self):
        """Providers reject empty text blocks; every adapter drops them and
        keeps the roles alternating."""
        for adapter in (AnthropicAdapter('k', 'm'), GeminiAdapter('k', 'm'), OpenAICompatAdapter('k', 'm')):
            with self.subTest(adapter=type(adapter).__name__):
                with patch(POST, return_value=fake_response(sse('[DONE]'))) as post:
                    list(adapter.stream('SYSTEM', TRANSCRIPT, TOOLS))
                payload = json.loads(post.call_args.kwargs['data'])
                wire = json.dumps(payload)
                self.assertNotIn('"text": ""', wire)
                messages = payload.get('messages') or payload.get('contents')
                roles = [message['role'] for message in messages if message['role'] != 'system']
                if not isinstance(adapter, OpenAICompatAdapter):
                    self.assertFalse([1 for left, right in zip(roles, roles[1:]) if left == right],
                                     "Roles alternate: %s" % roles)

    def test_network_failures_are_retryable(self):
        for error in (requests.ConnectionError("refused"), requests.Timeout("slow"),
                      requests.exceptions.ChunkedEncodingError("cut")):
            with self.subTest(error=type(error).__name__), patch(POST, side_effect=error), \
                    self.assertRaises(LLMError) as caught:
                list(OpenAICompatAdapter('k', 'm').stream('S', [{'role': 'user', 'content': 'Hi'}], TOOLS))
            self.assertTrue(caught.exception.retryable)

    def test_connection_lost_while_streaming(self):
        response = fake_response([])
        response.iter_lines.side_effect = requests.exceptions.ChunkedEncodingError("connection reset")
        with patch(POST, return_value=response), self.assertRaises(LLMError) as caught:
            list(GeminiAdapter('k', 'm').stream('S', [{'role': 'user', 'content': 'Hi'}], TOOLS))
        self.assertTrue(caught.exception.retryable)

    def test_error_bodies(self):
        """HTML error pages, empty bodies, lists and odd Retry-After values
        all give a readable error."""
        for status, body, headers, expected in (
                (502, ValueError, {}, '<html>Bad gateway</html>'),
                (500, ValueError, {}, 'Internal'),
                (400, [{'error': {'message': 'Gemini says no'}}], {}, 'Gemini says no'),
                (429, {'error': 'quota'}, {'Retry-After': 'Wed, 21 Oct 2026 07:28:00 GMT'}, 'quota'),
                (429, {'error': {'message': 'slow down'}}, {'Retry-After': '120'}, 'slow down')):
            with self.subTest(status=status, body=body):
                response = MagicMock(status_code=status, headers=headers, reason='Internal Server Error',
                                     text='<html>Bad gateway</html>' if status == 502 else '')
                response.json.side_effect = body if body is ValueError else None
                response.json.return_value = None if body is ValueError else body
                error = http_error(response, OpenAICompatAdapter._error_message(response))
                self.assertIn(expected, str(error))
                self.assertEqual(error.retryable, status in (429, 500, 502))
                self.assertTrue(error.retry_after is None or error.retry_after <= 10)

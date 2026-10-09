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
"""Wire-format tests of the provider adapters, against canned SSE streams."""
import json
from unittest.mock import MagicMock, patch

from odoo.tests import BaseCase, tagged

from odoo.addons.ai_accounting_analytics.llm import (
    AnthropicAdapter, GeminiAdapter, LLMError, OpenAICompatAdapter, OpenRouterAdapter, ToolCall,
)

TOOLS = [{'name': 'get_kpi_overview', 'description': 'KPIs',
          'parameters': {'type': 'object', 'properties': {'period': {'type': 'string'}}}}]


def sse(*events):
    """Build SSE lines; each event is ``data`` or ``(event_name, data)``."""
    lines = []
    for event in events:
        name, data = event if isinstance(event, tuple) else (None, event)
        if name:
            lines.append('event: %s' % name)
        lines.append('data: %s' % (data if isinstance(data, str) else json.dumps(data)))
        lines.append('')
    return lines


def fake_response(lines, status=200, body=None):
    response = MagicMock()
    response.status_code = status
    response.iter_lines.return_value = lines
    response.json.return_value = body or {}
    response.__enter__.return_value = response
    return response


def run(adapter, lines, messages=None, tools=TOOLS, allow_tools=True):
    with patch('odoo.addons.ai_accounting_analytics.llm.base.requests.post',
               return_value=fake_response(lines)) as post:
        events = list(adapter.stream('SYSTEM', messages or [{'role': 'user', 'content': 'Hi'}],
                                     tools, allow_tools))
    payload = json.loads(post.call_args.kwargs['data'])
    texts = [value for kind, value in events if kind == 'text']
    return payload, texts, events[-1][1], post


@tagged('-at_install', 'post_install')
class TestAdapters(BaseCase):

    def test_openai_text_tool_calls_and_usage(self):
        lines = sse(
            {'choices': [{'delta': {'content': 'Let me '}}]},
            {'choices': [{'delta': {'content': 'check.'}}]},
            {'choices': [{'delta': {'tool_calls': [{'index': 0, 'id': 'c1', 'function': {
                'name': 'get_kpi_overview', 'arguments': '{"period":'}}]}}]},
            {'choices': [{'delta': {'tool_calls': [{'index': 0, 'function': {
                'arguments': '"this_month"}'}}]}, 'finish_reason': 'tool_calls'}]},
            {'choices': [], 'usage': {'prompt_tokens': 1500, 'completion_tokens': 40,
                                      'prompt_tokens_details': {'cached_tokens': 1024}}},
            '[DONE]',
        )
        adapter = OpenAICompatAdapter('sk-x', 'gpt-4.1-mini', max_tokens=500)
        payload, texts, result, post = run(adapter, lines, allow_tools=False)
        self.assertEqual(texts, ['Let me ', 'check.'])
        self.assertEqual(result.tool_calls[0].arguments, {'period': 'this_month'})
        self.assertEqual((result.usage.input_tokens, result.usage.cached_tokens,
                          result.usage.output_tokens), (476, 1024, 40))
        self.assertEqual(payload['max_completion_tokens'], 500)
        self.assertEqual(payload['tool_choice'], 'none')
        self.assertTrue(payload['stream_options']['include_usage'])
        self.assertEqual(payload['messages'][0], {'role': 'system', 'content': 'SYSTEM'})
        self.assertEqual(post.call_args.args[0], 'https://api.openai.com/v1/chat/completions')
        self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer sk-x')

    def test_openai_tool_transcript(self):
        messages = [
            {'role': 'user', 'content': 'Hi'},
            {'role': 'assistant', 'content': '', 'tool_calls': [
                ToolCall(id='c1', name='get_kpi_overview', arguments={'period': 'today'})]},
            {'role': 'tool', 'results': [{'id': 'c1', 'name': 'get_kpi_overview',
                                          'content': '{"revenue":1}'}]},
        ]
        payload, _texts, _result, _post = run(
            OpenAICompatAdapter('k', 'm'), sse('[DONE]'), messages=messages)
        wire = payload['messages']
        self.assertEqual(wire[2]['tool_calls'][0]['function']['arguments'], '{"period": "today"}')
        self.assertEqual(wire[3], {'role': 'tool', 'tool_call_id': 'c1', 'content': '{"revenue":1}'})

    def test_openrouter_reported_cost(self):
        lines = sse({'choices': [{'delta': {'content': 'ok'}}],
                     'usage': {'prompt_tokens': 10, 'completion_tokens': 2, 'cost': 0.0012}},
                    '[DONE]')
        payload, _texts, result, post = run(OpenRouterAdapter('k', 'google/gemini-3.8-flash'), lines)
        self.assertAlmostEqual(result.usage.cost, 0.0012)
        self.assertIn('max_tokens', payload)
        self.assertTrue(post.call_args.args[0].startswith('https://openrouter.ai/api/v1'))

    def test_anthropic_stream(self):
        lines = sse(
            ('message_start', {'type': 'message_start', 'message': {'usage': {
                'input_tokens': 20, 'cache_read_input_tokens': 1800,
                'cache_creation_input_tokens': 0, 'output_tokens': 1}}}),
            ('content_block_start', {'type': 'content_block_start', 'index': 0,
                                     'content_block': {'type': 'thinking', 'thinking': ''}}),
            ('content_block_delta', {'type': 'content_block_delta', 'index': 0,
                                     'delta': {'type': 'thinking_delta', 'thinking': 'hmm'}}),
            ('content_block_delta', {'type': 'content_block_delta', 'index': 0,
                                     'delta': {'type': 'signature_delta', 'signature': 'sig'}}),
            ('content_block_start', {'type': 'content_block_start', 'index': 1,
                                     'content_block': {'type': 'text', 'text': ''}}),
            ('content_block_delta', {'type': 'content_block_delta', 'index': 1,
                                     'delta': {'type': 'text_delta', 'text': 'Checking.'}}),
            ('content_block_start', {'type': 'content_block_start', 'index': 2, 'content_block': {
                'type': 'tool_use', 'id': 'tu1', 'name': 'get_kpi_overview', 'input': {}}}),
            ('content_block_delta', {'type': 'content_block_delta', 'index': 2, 'delta': {
                'type': 'input_json_delta', 'partial_json': '{"period": "today"}'}}),
            ('message_delta', {'type': 'message_delta', 'delta': {'stop_reason': 'tool_use'},
                               'usage': {'output_tokens': 60}}),
            ('message_stop', {'type': 'message_stop'}),
        )
        adapter = AnthropicAdapter('sk-ant', 'claude-sonnet-5-5',
                                   extra_params={'output_config': {'effort': 'low'}})
        payload, texts, result, post = run(adapter, lines)
        self.assertEqual(texts, ['Checking.'])
        self.assertEqual(result.tool_calls[0].arguments, {'period': 'today'})
        self.assertEqual(result.raw[0], {'type': 'thinking', 'thinking': 'hmm', 'signature': 'sig'})
        self.assertEqual(result.raw[2]['input'], {'period': 'today'})
        self.assertEqual((result.usage.input_tokens, result.usage.cached_tokens,
                          result.usage.output_tokens), (20, 1800, 60))
        self.assertEqual(payload['system'][0]['cache_control'], {'type': 'ephemeral'})
        self.assertEqual(payload['output_config'], {'effort': 'low'})
        self.assertEqual(payload['tools'][0]['input_schema'], TOOLS[0]['parameters'])
        self.assertEqual(post.call_args.kwargs['headers']['anthropic-version'], '2023-06-01')

    def test_anthropic_transcript_echoes_raw_and_merges_roles(self):
        raw = [{'type': 'thinking', 'thinking': 't', 'signature': 's'},
               {'type': 'tool_use', 'id': 'tu1', 'name': 'get_kpi_overview', 'input': {}}]
        messages = [
            {'role': 'user', 'content': 'A'},
            {'role': 'user', 'content': 'B'},
            {'role': 'assistant', 'content': '', 'tool_calls': [], 'raw': raw},
            {'role': 'tool', 'results': [{'id': 'tu1', 'name': 'x', 'content': '{}',
                                          'is_error': True}]},
        ]
        payload, _texts, _result, _post = run(
            AnthropicAdapter('k', 'm'), sse(('message_stop', {'type': 'message_stop'})),
            messages=messages, allow_tools=False)
        wire = payload['messages']
        self.assertEqual([m['role'] for m in wire], ['user', 'assistant', 'user'])
        self.assertEqual(len(wire[0]['content']), 2)
        self.assertEqual(wire[1]['content'], raw)
        self.assertTrue(wire[2]['content'][0]['is_error'])
        self.assertEqual(payload['tool_choice'], {'type': 'none'})

    def test_anthropic_error_event(self):
        lines = sse(('error', {'type': 'error', 'error': {'message': 'Overloaded'}}))
        with self.assertRaises(LLMError):
            run(AnthropicAdapter('k', 'm'), lines)

    def test_gemini_stream_keeps_signatures(self):
        lines = sse(
            {'candidates': [{'content': {'parts': [{'text': 'Sure. '}]}}]},
            {'candidates': [{'content': {'parts': [{'functionCall': {
                'name': 'get_kpi_overview', 'args': {'period': 'this_month'}},
                'thoughtSignature': 'abc'}]}, 'finishReason': 'STOP'}],
             'usageMetadata': {'promptTokenCount': 900, 'cachedContentTokenCount': 300,
                               'candidatesTokenCount': 20, 'thoughtsTokenCount': 5}},
        )
        adapter = GeminiAdapter('AIza', 'gemini-3.8-flash', max_tokens=800, extra_params={
            'generationConfig': {'thinkingConfig': {'thinkingLevel': 'low'}}})
        payload, texts, result, post = run(adapter, lines)
        self.assertEqual(texts, ['Sure. '])
        self.assertEqual(result.tool_calls[0].arguments, {'period': 'this_month'})
        self.assertEqual(result.raw[1]['thoughtSignature'], 'abc')
        self.assertEqual((result.usage.input_tokens, result.usage.cached_tokens,
                          result.usage.output_tokens), (600, 300, 25))
        self.assertEqual(payload['generationConfig'], {
            'maxOutputTokens': 800, 'thinkingConfig': {'thinkingLevel': 'low'}})
        self.assertIn('gemini-3.8-flash:streamGenerateContent?alt=sse', post.call_args.args[0])
        self.assertEqual(post.call_args.kwargs['headers']['x-goog-api-key'], 'AIza')

    def test_gemini_transcript(self):
        raw = [{'functionCall': {'name': 'get_kpi_overview', 'args': {}}, 'thoughtSignature': 'abc'}]
        messages = [
            {'role': 'user', 'content': 'Hi'},
            {'role': 'assistant', 'content': '', 'tool_calls': [], 'raw': raw},
            {'role': 'tool', 'results': [{'id': '0', 'name': 'get_kpi_overview',
                                          'content': '{"revenue":5}'}]},
        ]
        payload, _texts, _result, _post = run(GeminiAdapter('k', 'm'), sse({}),
                                              messages=messages, allow_tools=False)
        contents = payload['contents']
        self.assertEqual(contents[1], {'role': 'model', 'parts': raw})
        self.assertEqual(contents[2]['parts'][0]['functionResponse'],
                         {'name': 'get_kpi_overview', 'response': {'revenue': 5}})
        self.assertEqual(payload['toolConfig'], {'functionCallingConfig': {'mode': 'NONE'}})

    def test_error_classification(self):
        from odoo.addons.ai_accounting_analytics.llm.base import stream_error
        self.assertTrue(LLMError("x", status_code=503).retryable)
        self.assertTrue(LLMError("network down").retryable)
        self.assertFalse(LLMError("x", status_code=401).retryable)
        self.assertFalse(LLMError("refused", retryable=False).retryable)
        self.assertEqual(stream_error({'code': 503, 'message': 'busy'}).status_code, 503)
        self.assertEqual(stream_error({'type': 'overloaded_error', 'message': 'busy'}).status_code, 529)

    def test_gemini_mid_stream_error_is_retryable(self):
        lines = sse({'candidates': [{'content': {'parts': [{'text': 'Acme '}]}}]},
                    {'error': {'code': 503, 'message': 'high demand', 'status': 'UNAVAILABLE'}})
        with self.assertRaises(LLMError) as caught:
            run(GeminiAdapter('k', 'm'), lines)
        self.assertTrue(caught.exception.retryable)

    def test_retry_after_header(self):
        response = fake_response([], status=429, body={'error': {'message': 'slow down'}})
        response.headers = {'Retry-After': '3'}
        with patch('odoo.addons.ai_accounting_analytics.llm.base.requests.post',
                   return_value=response):
            with self.assertRaises(LLMError) as caught:
                list(OpenAICompatAdapter('k', 'm').stream('S', [{'role': 'user', 'content': 'x'}], TOOLS))
        self.assertEqual(caught.exception.retry_after, 3.0)

    def test_http_error_message(self):
        response = fake_response([], status=400, body={'error': {'message': 'API key not valid'}})
        with patch('odoo.addons.ai_accounting_analytics.llm.base.requests.post',
                   return_value=response):
            with self.assertRaisesRegex(LLMError, 'API key not valid') as caught:
                list(GeminiAdapter('k', 'm').stream('S', [{'role': 'user', 'content': 'x'}], TOOLS))
        self.assertEqual(caught.exception.status_code, 400)

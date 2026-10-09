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
"""OpenAI Chat Completions adapter, also used for OpenRouter (and any
OpenAI-compatible endpoint set as the provider base URL)."""
import json

from .base import (
    BaseAdapter, LLMResult, ToolCall, Usage, deep_merge, parse_arguments,
    stream_error,
)


class OpenAICompatAdapter(BaseAdapter):
    default_base_url = 'https://api.openai.com/v1'
    max_tokens_key = 'max_completion_tokens'

    def _headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.api_key,
        }

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------
    @staticmethod
    def _wire_messages(system, messages):
        wire = [{'role': 'system', 'content': system}]
        for message in messages:
            role = message['role']
            if role == 'user':
                wire.append({'role': 'user', 'content': message['content']})
            elif role == 'assistant':
                item = {'role': 'assistant',
                        'content': message.get('content') or None}
                if message.get('tool_calls'):
                    item['tool_calls'] = [{
                        'id': call.id,
                        'type': 'function',
                        'function': {
                            'name': call.name,
                            'arguments': json.dumps(call.arguments),
                        },
                    } for call in message['tool_calls']]
                if item['content'] or item.get('tool_calls'):
                    wire.append(item)
            elif role == 'tool':
                for result in message['results']:
                    wire.append({
                        'role': 'tool',
                        'tool_call_id': result['id'],
                        'content': result['content'],
                    })
        return wire

    @staticmethod
    def _wire_tools(tools):
        return [{
            'type': 'function',
            'function': {
                'name': tool['name'],
                'description': tool['description'],
                'parameters': tool['parameters'],
            },
        } for tool in tools]

    def _payload(self, system, messages, tools, allow_tools):
        payload = {
            'model': self.model,
            'messages': self._wire_messages(system, messages),
            'stream': True,
            'stream_options': {'include_usage': True},
            self.max_tokens_key: self.max_tokens,
        }
        if tools:
            payload['tools'] = self._wire_tools(tools)
            if not allow_tools:
                payload['tool_choice'] = 'none'
        return deep_merge(payload, self.extra_params)

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------
    def stream(self, system, messages, tools, allow_tools=True):
        url = '%s/chat/completions' % self.base_url
        payload = self._payload(system, messages, tools, allow_tools)
        result = LLMResult()
        text_parts = []
        calls = {}
        for _event, data in self._post_sse(url, payload):
            if data == '[DONE]':
                break
            if not isinstance(data, dict):
                continue
            if data.get('error'):
                raise stream_error(data['error'])
            if data.get('usage'):
                result.usage = self._parse_usage(data['usage'])
            for choice in data.get('choices') or []:
                delta = choice.get('delta') or {}
                if delta.get('content'):
                    text_parts.append(delta['content'])
                    yield 'text', delta['content']
                for call_delta in delta.get('tool_calls') or []:
                    index = call_delta.get('index')
                    if index is None:
                        # Some compatible endpoints omit the index: a new id
                        # starts a new call, chunks without one continue it.
                        index = max(calls, default=0)
                        if call_delta.get('id') and calls.get(index, {}).get('id') \
                                and call_delta['id'] != calls[index]['id']:
                            index += 1
                    call = calls.setdefault(index, {'id': '', 'name': '', 'args': ''})
                    call['id'] = call_delta.get('id') or call['id']
                    function = call_delta.get('function') or {}
                    call['name'] += function.get('name') or ''
                    call['args'] += function.get('arguments') or ''
                if choice.get('finish_reason'):
                    result.stop_reason = choice['finish_reason']
        result.text = ''.join(text_parts)
        for index in sorted(calls):
            call = calls[index]
            arguments, ok = parse_arguments(call['args'])
            result.tool_calls.append(ToolCall(
                id=call['id'] or 'call_%s' % index, name=call['name'],
                arguments=arguments, invalid_arguments=not ok))
        yield 'done', result

    @staticmethod
    def _parse_usage(usage):
        prompt = usage.get('prompt_tokens') or 0
        cached = (usage.get('prompt_tokens_details') or {}).get('cached_tokens') or 0
        cost = usage.get('cost')
        return Usage(
            input_tokens=max(prompt - cached, 0),
            cached_tokens=cached,
            output_tokens=usage.get('completion_tokens') or 0,
            cost=float(cost) if cost is not None else None,
        )

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------
    def list_models(self):
        data = self._get('%s/models' % self.base_url)
        models = []
        for item in data.get('data') or []:
            pricing = item.get('pricing') or {}
            models.append({
                'technical_name': item['id'],
                'name': item.get('name') or item['id'],
                'price_input': self._per_million(pricing.get('prompt')),
                'price_output': self._per_million(pricing.get('completion')),
                'price_cached': self._per_million(pricing.get('input_cache_read')),
            })
        return models

    @staticmethod
    def _per_million(per_token):
        try:
            return round(float(per_token) * 1_000_000, 6)
        except (TypeError, ValueError):
            return None


class OpenRouterAdapter(OpenAICompatAdapter):
    default_base_url = 'https://openrouter.ai/api/v1'
    max_tokens_key = 'max_tokens'

    def _headers(self):
        headers = super()._headers()
        headers['X-Title'] = 'Odoo AI Accounting Analytics'
        return headers

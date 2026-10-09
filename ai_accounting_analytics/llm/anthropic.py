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
"""Anthropic (Claude) Messages API adapter.

Raw HTTP keeps the module free of provider SDKs, like the other adapters.
"""
from .base import (
    BaseAdapter, LLMError, LLMResult, ToolCall, Usage, deep_merge,
    parse_arguments, stream_error,
)

ANTHROPIC_VERSION = '2023-06-01'


class AnthropicAdapter(BaseAdapter):
    default_base_url = 'https://api.anthropic.com/v1'

    def _headers(self):
        return {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': ANTHROPIC_VERSION,
        }

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------
    def _wire_messages(self, messages):
        wire = []
        for message in messages:
            role = message['role']
            if role == 'user':
                wire.append({'role': 'user', 'content': [
                    {'type': 'text', 'text': message['content']}]})
            elif role == 'assistant':
                if message.get('raw'):
                    # Echo thinking / tool_use blocks back unchanged.
                    content = message['raw']
                else:
                    content = []
                    if message.get('content'):
                        content.append({'type': 'text', 'text': message['content']})
                    for call in message.get('tool_calls') or []:
                        content.append({'type': 'tool_use', 'id': call.id,
                                        'name': call.name, 'input': call.arguments})
                if content:
                    wire.append({'role': 'assistant', 'content': content})
            elif role == 'tool':
                wire.append({'role': 'user', 'content': [{
                    'type': 'tool_result',
                    'tool_use_id': result['id'],
                    'content': result['content'],
                    **({'is_error': True} if result.get('is_error') else {}),
                } for result in message['results']]})
        return self._merge_same_roles(wire)

    def _payload(self, system, messages, tools, allow_tools):
        payload = {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'stream': True,
            # The stable prefix (tools + system prompt) is cached explicitly;
            # the top-level marker additionally caches the growing transcript
            # so every extra agent step re-reads the previous ones at the
            # cache price.
            'system': [{'type': 'text', 'text': system,
                        'cache_control': {'type': 'ephemeral'}}],
            'cache_control': {'type': 'ephemeral'},
            'messages': self._wire_messages(messages),
        }
        if tools:
            payload['tools'] = [{
                'name': tool['name'],
                'description': tool['description'],
                'input_schema': tool['parameters'],
            } for tool in tools]
            if not allow_tools:
                payload['tool_choice'] = {'type': 'none'}
        return deep_merge(payload, self.extra_params)

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------
    def stream(self, system, messages, tools, allow_tools=True):
        url = '%s/messages' % self.base_url
        payload = self._payload(system, messages, tools, allow_tools)
        result = LLMResult()
        usage = {}
        blocks = {}
        for _event, data in self._post_sse(url, payload):
            if not isinstance(data, dict):
                continue
            kind = data.get('type')
            if kind == 'message_start':
                usage.update((data.get('message') or {}).get('usage') or {})
            elif kind == 'content_block_start':
                block = dict(data.get('content_block') or {})
                if block.get('type') == 'tool_use':
                    block['_json'] = ''
                blocks[data.get('index', len(blocks))] = block
            elif kind == 'content_block_delta':
                block = blocks.setdefault(data.get('index', 0), {'type': 'text', 'text': ''})
                delta = data.get('delta') or {}
                delta_type = delta.get('type')
                if delta_type == 'text_delta':
                    block['text'] = block.get('text', '') + delta.get('text', '')
                    yield 'text', delta.get('text', '')
                elif delta_type == 'input_json_delta':
                    block['_json'] = block.get('_json', '') + delta.get('partial_json', '')
                elif delta_type == 'thinking_delta':
                    block['thinking'] = block.get('thinking', '') + delta.get('thinking', '')
                elif delta_type == 'signature_delta':
                    block['signature'] = block.get('signature', '') + delta.get('signature', '')
            elif kind == 'message_delta':
                result.stop_reason = (data.get('delta') or {}).get('stop_reason') or result.stop_reason
                usage.update(data.get('usage') or {})
            elif kind == 'error':
                raise stream_error(data.get('error') or data)

        raw = []
        text_parts = []
        for index in sorted(blocks):
            block = blocks[index]
            if block.get('type') == 'tool_use':
                arguments, ok = parse_arguments(block.pop('_json', '') or block.get('input'))
                block['input'] = arguments
                result.tool_calls.append(ToolCall(
                    id=block['id'], name=block['name'], arguments=arguments,
                    invalid_arguments=not ok))
            elif block.get('type') == 'text':
                text_parts.append(block.get('text', ''))
                block = {'type': 'text', 'text': block.get('text', '')}
                if not block['text']:
                    continue
            raw.append(block)
        result.text = ''.join(text_parts)
        result.raw = raw
        result.usage = Usage(
            input_tokens=usage.get('input_tokens') or 0,
            cached_tokens=usage.get('cache_read_input_tokens') or 0,
            cache_write_tokens=usage.get('cache_creation_input_tokens') or 0,
            output_tokens=usage.get('output_tokens') or 0,
        )
        if result.stop_reason == 'refusal':
            raise LLMError('The model declined to answer this request.', retryable=False)
        yield 'done', result

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------
    def list_models(self):
        data = self._get('%s/models' % self.base_url, params={'limit': 100})
        return [{
            'technical_name': item['id'],
            'name': item.get('display_name') or item['id'],
            'price_input': None,
            'price_output': None,
            'price_cached': None,
        } for item in data.get('data') or []]

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
"""Google Gemini (Generative Language API) adapter."""
import json

from .base import BaseAdapter, LLMError, LLMResult, ToolCall, Usage, deep_merge, stream_error


class GeminiAdapter(BaseAdapter):
    default_base_url = 'https://generativelanguage.googleapis.com/v1beta'

    def _headers(self):
        return {'Content-Type': 'application/json',
                'x-goog-api-key': self.api_key}

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------
    @staticmethod
    def _function_response(content):
        try:
            value = json.loads(content)
        except (TypeError, ValueError):
            value = content
        return value if isinstance(value, dict) else {'result': value}

    def _wire_contents(self, messages):
        contents = []
        for message in messages:
            role = message['role']
            if role == 'user':
                contents.append({'role': 'user', 'parts': [{'text': message['content']}]})
            elif role == 'assistant':
                if message.get('raw'):
                    # Parts are echoed unchanged: they carry the thought
                    # signatures Gemini requires back inside a tool loop.
                    parts = message['raw']
                else:
                    parts = []
                    if message.get('content'):
                        parts.append({'text': message['content']})
                    for call in message.get('tool_calls') or []:
                        parts.append({'functionCall': {'name': call.name,
                                                       'args': call.arguments}})
                if parts:
                    contents.append({'role': 'model', 'parts': parts})
            elif role == 'tool':
                contents.append({'role': 'user', 'parts': [{
                    'functionResponse': {
                        'name': result['name'],
                        'response': self._function_response(result['content']),
                    },
                } for result in message['results']]})
        return self._merge_same_roles(contents, content_key='parts')

    def _payload(self, system, messages, tools, allow_tools):
        payload = {
            'systemInstruction': {'parts': [{'text': system}]},
            'contents': self._wire_contents(messages),
            'generationConfig': {'maxOutputTokens': self.max_tokens},
        }
        if tools:
            payload['tools'] = [{'functionDeclarations': [{
                'name': tool['name'],
                'description': tool['description'],
                'parameters': tool['parameters'],
            } for tool in tools]}]
            if not allow_tools:
                payload['toolConfig'] = {'functionCallingConfig': {'mode': 'NONE'}}
        return deep_merge(payload, self.extra_params)

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------
    def stream(self, system, messages, tools, allow_tools=True):
        url = '%s/models/%s:streamGenerateContent?alt=sse' % (self.base_url, self.model)
        payload = self._payload(system, messages, tools, allow_tools)
        result = LLMResult()
        raw = []
        text_parts = []
        usage = {}
        for _event, data in self._post_sse(url, payload):
            if not isinstance(data, dict):
                continue
            if data.get('error'):
                raise stream_error(data['error'])
            block_reason = (data.get('promptFeedback') or {}).get('blockReason')
            if block_reason:
                raise LLMError('The request was blocked by the provider (%s).' % block_reason,
                               retryable=False)
            if data.get('usageMetadata'):
                usage = data['usageMetadata']
            for candidate in data.get('candidates') or []:
                for part in (candidate.get('content') or {}).get('parts') or []:
                    if part.get('thought'):
                        continue
                    raw.append(part)
                    if part.get('text'):
                        text_parts.append(part['text'])
                        yield 'text', part['text']
                    if part.get('functionCall'):
                        call = part['functionCall']
                        result.tool_calls.append(ToolCall(
                            id=call.get('id') or 'call_%s' % len(result.tool_calls),
                            name=call.get('name', ''),
                            arguments=call.get('args') or {}))
                if candidate.get('finishReason'):
                    result.stop_reason = candidate['finishReason']
                    if result.stop_reason in ('MALFORMED_FUNCTION_CALL', 'UNEXPECTED_TOOL_CALL'):
                        # A broken generation, not a refusal: worth a retry.
                        raise LLMError('The model produced an invalid tool call (%s).' % result.stop_reason,
                                       retryable=True)
        result.text = ''.join(text_parts)
        result.raw = raw
        prompt = usage.get('promptTokenCount') or 0
        cached = usage.get('cachedContentTokenCount') or 0
        result.usage = Usage(
            input_tokens=max(prompt - cached, 0),
            cached_tokens=cached,
            output_tokens=(usage.get('candidatesTokenCount') or 0)
            + (usage.get('thoughtsTokenCount') or 0),
        )
        yield 'done', result

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------
    def list_models(self):
        data = self._get('%s/models' % self.base_url, params={'pageSize': 1000})
        models = []
        for item in data.get('models') or []:
            if 'generateContent' not in (item.get('supportedGenerationMethods') or []):
                continue
            models.append({
                'technical_name': item['name'].removeprefix('models/'),
                'name': item.get('displayName') or item['name'],
                'price_input': None,
                'price_output': None,
                'price_cached': None,
            })
        return models

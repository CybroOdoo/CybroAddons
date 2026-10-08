# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

"""Minimal client translating Odoo AI messages to an OpenAI-compatible API.

Odoo AI message format (see odoo.addons.ai.utils.types):
    user:      {'role': 'user', 'content': [text | inline_data | tool_result parts]}
    assistant: {'role': 'assistant', 'content': [text | inline_data | tool_call parts]}
"""
import json
import logging
import time
from urllib.parse import urlparse

import requests
from urllib3.exceptions import NewConnectionError

_logger = logging.getLogger(__name__)

PARAM_PREFIX = 'ai_custom_provider.'
# ai.embedding.embedding_vector is a Vector(size=1536) column
EMBEDDING_DIMENSIONS = 1536
# Retries only for failures where the request never reached the provider
CONNECT_ATTEMPTS = 3
CONNECT_RETRY_DELAY = 1.0  # seconds, multiplied by the attempt number


class ProviderError(Exception):
    pass


def get_provider_config(env):
    """Snapshot the provider settings into a plain dict (usable outside a cursor)."""
    ICP = env['ir.config_parameter'].sudo()
    enabled = ICP.get_bool(PARAM_PREFIX + 'enabled')
    provider = env['ai.custom.provider'].sudo().browse(ICP.get_int(PARAM_PREFIX + 'provider_id')).exists()
    if not enabled or not provider:
        # Falls back to Odoo IAP when no provider is selected.
        return {'enabled': False}
    Model = env['ai.custom.provider.model'].sudo()
    chat_model = Model.browse(ICP.get_int(PARAM_PREFIX + 'model_id')).exists()
    reasoning_model = Model.browse(ICP.get_int(PARAM_PREFIX + 'reasoning_model_id')).exists()
    embedding_model = Model.browse(ICP.get_int(PARAM_PREFIX + 'embedding_model_id')).exists()
    return {
        'enabled': True,
        'provider': provider.name,
        'base_url': provider.base_url.rstrip('/'),
        'api_key': provider.api_key or '',
        'model': chat_model.name or '',
        'reasoning_model': reasoning_model.name or '',
        'embedding_model': embedding_model.name or '',
        'send_embedding_dimensions': provider.send_embedding_dimensions,
        'timeout': ICP.get_int(PARAM_PREFIX + 'timeout') or 120,
    }


def _never_sent(error):
    """True when the request failed before reaching the provider (DNS, refused, connect timeout)."""
    if isinstance(error, requests.exceptions.ConnectTimeout):
        return True
    if isinstance(error, requests.exceptions.ConnectionError):
        reason = getattr(error.args[0], 'reason', None) if error.args else None
        return isinstance(reason, NewConnectionError)  # includes NameResolutionError
    return False


def _post(config, path, payload):
    headers = {'Content-Type': 'application/json'}
    if config['api_key']:
        headers['Authorization'] = f"Bearer {config['api_key']}"
    url = f"{config['base_url']}/{path}"
    _logger.info("AI custom provider request %s (model=%s)", url, payload.get('model'))
    for attempt in range(1, CONNECT_ATTEMPTS + 1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=config['timeout'])
            break
        except requests.exceptions.RequestException as e:
            if _never_sent(e) and attempt < CONNECT_ATTEMPTS:
                # DNS hiccup / refused connection: the provider never got the
                # request, so retrying cannot double-bill.
                _logger.warning("AI custom provider: could not connect to %s (attempt %s/%s), retrying: %s",
                                url, attempt, CONNECT_ATTEMPTS, e)
                time.sleep(CONNECT_RETRY_DELAY * attempt)
                continue
            if _never_sent(e):
                host = urlparse(url).hostname
                raise ProviderError(
                    f"Could not connect to the AI provider ({host}) after {attempt} attempts. "
                    "The Odoo server could not resolve or reach this address: check its internet/DNS "
                    "connection and the provider's API Base URL."
                ) from e
            raise ProviderError(f"Could not reach the AI provider at {url}: {e}") from e
    if response.status_code >= 400:
        try:
            detail = response.json().get('error', response.text)
            if isinstance(detail, dict):
                detail = detail.get('message') or json.dumps(detail)
        except ValueError:
            detail = response.text
        raise ProviderError(f"AI provider error {response.status_code}: {str(detail)[:500]}")
    return response.json()


# ---------------------------------------------------------------------------
# Odoo -> OpenAI
# ---------------------------------------------------------------------------

def _parts_to_text(parts):
    return '\n'.join(p.get('text', '') for p in parts or [] if p.get('type') == 'text')


def _inline_data_to_openai(part):
    mimetype = part.get('mimetype') or 'application/octet-stream'
    data_uri = f"data:{mimetype};base64,{part['data']}"
    if mimetype.startswith('image/'):
        return {'type': 'image_url', 'image_url': {'url': data_uri}}
    if mimetype == 'application/pdf':
        return {'type': 'file', 'file': {'filename': 'document.pdf', 'file_data': data_uri}}
    return {'type': 'text', 'text': f"[Attached file of type {mimetype} omitted: not supported by this provider]"}


def _user_message_to_openai(message):
    """A single Odoo user message can hold tool results and regular parts.

    OpenAI expects tool results as separate 'tool' messages placed right after
    the assistant message that issued the calls, so those come first.
    """
    result = []
    extra_parts = []  # images returned by tools cannot live in a 'tool' message
    content = []
    for part in message['content']:
        ptype = part.get('type')
        if ptype == 'tool_result':
            tool_parts = part.get('result') or []
            text = _parts_to_text(tool_parts)
            if not part.get('success', True) and not text.startswith('Error'):
                text = f"Error: {text}"
            result.append({
                'role': 'tool',
                'tool_call_id': str(part['tool_call_id']),
                'content': text or ('success' if part.get('success', True) else 'Error'),
            })
            extra_parts += [_inline_data_to_openai(p) for p in tool_parts if p.get('type') == 'inline_data']
        elif ptype == 'text':
            content.append({'type': 'text', 'text': part['text']})
        elif ptype == 'inline_data':
            content.append(_inline_data_to_openai(part))
    content = extra_parts + content
    if content:
        result.append({'role': 'user', 'content': content})
    return result


def _assistant_message_to_openai(message):
    text = []
    tool_calls = []
    for part in message['content']:
        if part.get('type') == 'text':
            text.append(part['text'])
        elif part.get('type') == 'tool_call':
            tool_calls.append({
                'id': str(part['call_id']),
                'type': 'function',
                'function': {
                    'name': part['name'],
                    'arguments': json.dumps(part.get('args') or {}),
                },
            })
    msg = {'role': 'assistant', 'content': '\n'.join(text) or None}
    if tool_calls:
        msg['tool_calls'] = tool_calls
    return msg


def to_strict_schema(schema):
    """Make a JSON schema compatible with strict structured outputs.

    Strict mode (required by Anthropic, recommended by OpenAI) needs every
    object to list all its properties as required and to forbid additional
    properties; originally optional properties become nullable instead.
    """
    if isinstance(schema, list):
        return [to_strict_schema(s) for s in schema]
    if not isinstance(schema, dict):
        return schema
    schema = {key: to_strict_schema(value) if key in ('items', 'anyOf', 'oneOf', 'allOf') else value
              for key, value in schema.items()}
    types = schema.get('type')
    if types == 'object' or (isinstance(types, list) and 'object' in types) or 'properties' in schema:
        properties = {name: to_strict_schema(prop) for name, prop in (schema.get('properties') or {}).items()}
        required = set(schema.get('required') or [])
        for name, prop in properties.items():
            if name not in required:
                properties[name] = _make_nullable(prop)
        schema['properties'] = properties
        schema['required'] = list(properties)
        schema['additionalProperties'] = False
    return schema


def _make_nullable(prop):
    prop = dict(prop)
    types = prop.get('type')
    if isinstance(types, str) and types != 'null':
        prop['type'] = [types, 'null']
    elif isinstance(types, list) and 'null' not in types:
        prop['type'] = [*types, 'null']
    elif types is None and 'anyOf' in prop:
        prop['anyOf'] = [*prop['anyOf'], {'type': 'null'}]
    return prop


def build_chat_payload(config, messages, instructions, tools=None, **options):
    if options.get('image_generation'):
        raise ProviderError("Image generation is not supported by the custom AI provider.")
    oa_messages = []
    if instructions:
        oa_messages.append({'role': 'system', 'content': instructions})
    for message in messages:
        if message['role'] == 'assistant':
            oa_messages.append(_assistant_message_to_openai(message))
        else:
            oa_messages.extend(_user_message_to_openai(message))

    model = config['model']
    if not model:
        raise ProviderError(
            f"No chat model is configured for the AI provider '{config.get('provider')}'. "
            "Select one in Settings > AI Provider."
        )
    if options.get('boost_reasoning') and config['reasoning_model']:
        model = config['reasoning_model']
    payload = {'model': model, 'messages': oa_messages}
    if tools:
        payload['tools'] = [{
            'type': 'function',
            'function': {
                'name': tool['name'],
                'description': tool.get('instructions') or '',
                'parameters': tool.get('schema') or {'type': 'object', 'properties': {}},
            },
        } for tool in tools]
    if schema := options.get('schema'):
        payload['response_format'] = {
            'type': 'json_schema',
            'json_schema': {'name': 'response', 'schema': to_strict_schema(schema), 'strict': True},
        }
    # 'web_grounding', 'usage' and 'aspect_ratio' are Odoo-server specific: ignored.
    return payload


# ---------------------------------------------------------------------------
# OpenAI -> Odoo
# ---------------------------------------------------------------------------

def parse_chat_response(data):
    choices = data.get('choices') or []
    if not choices:
        raise ProviderError(f"AI provider returned no choices: {str(data)[:500]}")
    message = choices[0].get('message') or {}
    content = []
    text = message.get('content')
    if isinstance(text, list):  # some providers return content parts
        text = '\n'.join(p.get('text', '') for p in text if isinstance(p, dict))
    if text:
        content.append({'type': 'text', 'text': text})
    for call in message.get('tool_calls') or []:
        function = call.get('function') or {}
        raw_args = function.get('arguments') or '{}'
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            _logger.warning("AI custom provider: invalid tool arguments %r", raw_args)
            args = {}
        content.append({
            'type': 'tool_call',
            'name': function.get('name'),
            'args': args or {},
            'call_id': call.get('id'),
        })
    if not content:
        content.append({'type': 'text', 'text': ''})
    return {
        'result': {
            'role': 'assistant',
            'content': content,
            'provider_metadata': {
                'provider': 'ai_custom_provider',
                'model': data.get('model'),
                'usage': data.get('usage'),
            },
        },
    }


def get_completions(config, messages, instructions, tools=None, **options):
    payload = build_chat_payload(config, messages, instructions, tools, **options)
    return parse_chat_response(_post(config, 'chat/completions', payload))


def get_embeddings(config, inputs, model=None):
    model = model or config['embedding_model']
    if not model:
        raise ProviderError(
            f"No embedding model is configured for the AI provider '{config.get('provider')}'. "
            "Select one in Settings > AI Provider, or remove the sources of your AI agents."
        )
    texts = []
    for item in inputs:
        if item.get('title'):
            texts.append(f"{item['title']}\n\n{item.get('content') or ''}")
        else:
            texts.append(item.get('content') or '')
    payload = {'model': model, 'input': texts}
    if config['send_embedding_dimensions']:
        payload['dimensions'] = EMBEDDING_DIMENSIONS
    data = _post(config, 'embeddings', payload)
    vectors = [row['embedding'] for row in sorted(data.get('data', []), key=lambda r: r.get('index', 0))]
    if len(vectors) != len(texts):
        raise ProviderError("AI provider returned an unexpected number of embeddings.")
    if vectors and len(vectors[0]) != EMBEDDING_DIMENSIONS:
        raise ProviderError(
            f"Embedding model returned {len(vectors[0])} dimensions, Odoo requires {EMBEDDING_DIMENSIONS}. "
            "Use a model supporting 1536 dimensions (e.g. text-embedding-3-small)."
        )
    return {'embeddings': vectors}

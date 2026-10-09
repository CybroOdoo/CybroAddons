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
"""Provider-neutral plumbing shared by the LLM adapters.

Adapters speak each provider's HTTP API directly with ``requests`` (no SDK
dependency) and translate between a small provider-neutral transcript format
and the provider wire format.

Transcript format (list of dicts)::

    {'role': 'user', 'content': str}
    {'role': 'assistant', 'content': str, 'tool_calls': [ToolCall], 'raw': any}
    {'role': 'tool', 'results': [{'id', 'name', 'content': str, 'is_error'}]}

``raw`` holds the provider's own representation of an assistant turn (e.g.
Claude thinking blocks or Gemini thought signatures) which must be echoed back
unchanged inside the same agent loop.

Tool definitions are ``{'name', 'description', 'parameters'}`` where
``parameters`` is a plain JSON schema (type/properties/enum/required/items).

``stream()`` yields ``('text', str)`` events while the answer is generated and
finally one ``('done', LLMResult)`` event.
"""
import json
import logging
from dataclasses import dataclass, field

import requests

from .arguments import parse_json

_logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 120


# Temporary provider conditions worth retrying: timeouts, rate limits and
# overload (529 is Anthropic's "overloaded").
RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}
MAX_RETRY_AFTER = 10


class LLMError(Exception):
    """Error reported by (or while talking to) an AI provider.

    ``retryable`` defaults to True for network errors (no status) and for
    the temporary HTTP statuses above; ``retry_after`` is the provider's
    hint in seconds, when it sends one.
    """

    def __init__(self, message, status_code=None, retryable=None, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = (status_code is None or status_code in RETRYABLE_STATUS) \
            if retryable is None else retryable
        self.retry_after = retry_after


def http_error(response, message):
    """LLMError for a failed HTTP response, with its Retry-After hint."""
    retry_after = None
    try:
        retry_after = min(float(response.headers.get('Retry-After')), MAX_RETRY_AFTER)
    except (TypeError, ValueError):
        pass
    return LLMError('%s: %s' % (response.status_code, message),
                    status_code=response.status_code, retry_after=retry_after)


def stream_error(error):
    """LLMError for an error object sent inside an event stream."""
    if not isinstance(error, dict):
        return LLMError(str(error))
    code = error.get('code') if isinstance(error.get('code'), int) else None
    if code is None and error.get('type') in ('overloaded_error', 'rate_limit_error', 'api_error'):
        code = {'overloaded_error': 529, 'rate_limit_error': 429, 'api_error': 500}[error['type']]
    message = error.get('message') or str(error)
    return LLMError('%s: %s' % (code, message) if code else message, status_code=code)


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict = field(default_factory=dict)
    invalid_arguments: bool = False


@dataclass
class Usage:
    input_tokens: int = 0          # uncached prompt tokens
    cached_tokens: int = 0         # prompt tokens served from cache
    cache_write_tokens: int = 0    # prompt tokens written to cache
    output_tokens: int = 0         # completion tokens, reasoning included
    cost: float | None = None      # provider-reported cost (USD), if any


@dataclass
class LLMResult:
    text: str = ''
    tool_calls: list = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    raw: object = None
    stop_reason: str | None = None


def deep_merge(base, extra):
    """Recursively merge ``extra`` into a copy of ``base``."""
    result = dict(base)
    for key, value in (extra or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def parse_arguments(raw_arguments):
    """Parse a tool-call argument string; ``(dict, ok)``. Accepts ``null``,
    double-encoded JSON and Python literals, which some models produce."""
    if isinstance(raw_arguments, dict):
        return raw_arguments, True
    if raw_arguments is None or (isinstance(raw_arguments, str) and not raw_arguments.strip()):
        return {}, True
    if not isinstance(raw_arguments, str):
        return {}, False
    if raw_arguments.strip() == 'null':
        return {}, True
    value = parse_json(raw_arguments)
    return (value, True) if isinstance(value, dict) else ({}, False)


class BaseAdapter:
    """Base class of the provider adapters."""

    default_base_url = ''

    def __init__(self, api_key, model, base_url=None, max_tokens=1024,
                 extra_params=None):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or self.default_base_url).rstrip('/')
        self.max_tokens = max_tokens
        self.extra_params = extra_params or {}
        # Seconds to wait for the provider; lowered to fit the answer's time
        # budget (see AiAccountingChat._ai_call_model).
        self.read_timeout = READ_TIMEOUT

    # ------------------------------------------------------------------
    # API to implement
    # ------------------------------------------------------------------
    def stream(self, system, messages, tools, allow_tools=True):
        raise NotImplementedError()

    def list_models(self):
        """Return ``[{'technical_name', 'name', 'price_input', 'price_output',
        'price_cached'}]`` (prices per million tokens, when known)."""
        raise NotImplementedError()

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------
    def _headers(self):
        return {'Content-Type': 'application/json'}

    @staticmethod
    def _error_message(response):
        try:
            payload = response.json()
        except ValueError:
            return response.text[:300] or response.reason
        if isinstance(payload, list) and payload:
            payload = payload[0]
        error = payload.get('error') if isinstance(payload, dict) else None
        if isinstance(error, dict):
            return error.get('message') or json.dumps(error)[:300]
        return str(error or payload)[:300]

    def _get(self, url, params=None):
        try:
            response = requests.get(
                url, headers=self._headers(), params=params,
                timeout=(CONNECT_TIMEOUT, self.read_timeout))
        except requests.RequestException as error:
            raise LLMError(str(error)) from error
        if response.status_code >= 400:
            raise http_error(response, self._error_message(response))
        return response.json()

    def _post_sse(self, url, payload):
        """POST ``payload`` and yield ``(event_name, data)`` for every
        server-sent event; ``data`` is the decoded JSON (or the raw string
        when it is not JSON, e.g. OpenAI's ``[DONE]``)."""
        try:
            response = requests.post(
                url, headers=self._headers(), data=json.dumps(payload),
                stream=True, timeout=(CONNECT_TIMEOUT, self.read_timeout))
        except requests.RequestException as error:
            raise LLMError(str(error)) from error
        with response:
            if response.status_code >= 400:
                raise http_error(response, self._error_message(response))
            response.encoding = 'utf-8'
            event_name, data_lines = None, []
            try:
                for line in response.iter_lines(decode_unicode=True):
                    if line is None:
                        continue
                    line = line.rstrip('\r')
                    if not line:
                        if data_lines:
                            yield event_name, self._decode('\n'.join(data_lines))
                        event_name, data_lines = None, []
                    elif line.startswith('event:'):
                        event_name = line[6:].strip()
                    elif line.startswith('data:'):
                        data_lines.append(line[5:].lstrip())
                if data_lines:
                    yield event_name, self._decode('\n'.join(data_lines))
            except requests.RequestException as error:
                raise LLMError(str(error)) from error

    @staticmethod
    def _decode(data):
        try:
            return json.loads(data)
        except ValueError:
            return data

    @staticmethod
    def _merge_same_roles(messages, role_key='role', content_key='content'):
        """Merge consecutive wire messages sharing a role (providers that
        require strictly alternating turns)."""
        merged = []
        for message in messages:
            if merged and merged[-1][role_key] == message[role_key]:
                previous = merged[-1][content_key]
                current = message[content_key]
                merged[-1] = dict(merged[-1], **{content_key: previous + current})
            else:
                merged.append(dict(message))
        return merged

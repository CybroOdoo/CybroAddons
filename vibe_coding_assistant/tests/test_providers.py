# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: FATHIMA SHALFA P (odoo@cybrosys.com)
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
###############################################################################
"""Tests for the Gemini, Claude and OpenAI adapters with HTTP mocked out."""
from unittest.mock import MagicMock, patch

import requests

from odoo.tests import TransactionCase, tagged

from ..services.provider_base import (
    AIAuthError,
    AINetworkError,
    AINotFoundError,
    AIProviderBase,
    AIProviderError,
    AIQuotaError,
    classify_http_error,
    get_provider,
)
from ..services.provider_claude import ClaudeProvider
from ..services.provider_gemini import GeminiProvider
from ..services.provider_openai import OpenAIProvider

BASE = "odoo.addons.vibe_coding_assistant.services.provider_%s.requests"


def _response(status=200, payload=None, text=""):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload or {}
    resp.text = text
    resp.content = text.encode() or b"{}"
    return resp


@tagged("post_install", "-at_install")
class TestProviderBase(TransactionCase):

    def test_classify_http_error(self):
        self.assertIsInstance(classify_http_error(429, "x"), AIQuotaError)
        self.assertIsInstance(classify_http_error(401, "x"), AIAuthError)
        self.assertIsInstance(classify_http_error(403, "x"), AIAuthError)
        self.assertIsInstance(classify_http_error(404, "x"), AINotFoundError)
        err = classify_http_error(500, "boom")
        self.assertIs(type(err), AIProviderError)
        self.assertIn("500", str(err))

    def test_factory(self):
        self.assertIsInstance(get_provider("gemini", "k", "m", "https://g/"), GeminiProvider)
        self.assertIsInstance(get_provider("claude", "k", "m", "https://c"), ClaudeProvider)
        self.assertIsInstance(get_provider("openai", "k", "m", "https://o"), OpenAIProvider)
        self.assertEqual(get_provider("gemini", "k", "m", "https://g/").base_url, "https://g")
        with self.assertRaises(AIProviderError):
            get_provider("unknown", "k", "m", "https://x")

    def test_base_ping_and_list_models(self):
        class Dummy(AIProviderBase):
            code = "dummy"

            def generate(self, system_prompt, user_prompt):
                return "OK", {}

        provider = Dummy("k", "m", "https://d")
        self.assertEqual(provider.ping(), "OK")
        with self.assertRaises(NotImplementedError):
            provider.list_models()


class AdapterMixin:
    """Shared assertions run against each adapter."""

    # Odoo's loader skips inherited test methods unless this is set.
    allow_inherited_tests_method = True

    code = None
    cls = None
    generate_payload = None
    generate_usage = None
    list_payload = None
    list_expected = None
    ping_payload = None
    ping_method = "post"

    def setUp(self):
        super().setUp()
        self.provider = self.cls("secret", "model-x", "https://api.example.com/v1/")
        patcher = patch(BASE % self.code)
        self.requests = patcher.start()
        self.requests.RequestException = requests.RequestException
        self.addCleanup(patcher.stop)

    def test_generate_success(self):
        self.requests.post.return_value = _response(payload=self.generate_payload)
        text, usage = self.provider.generate("system", "user")
        self.assertEqual(text, "{}")
        self.assertEqual(usage, self.generate_usage)

    def test_generate_usage_missing(self):
        payload = {k: v for k, v in self.generate_payload.items()
                   if k not in ("usage", "usageMetadata")}
        self.requests.post.return_value = _response(payload=payload)
        _text, usage = self.provider.generate("system", "user")
        self.assertEqual(usage, {"input": 0, "output": 0, "total": 0})

    def test_generate_http_error(self):
        self.requests.post.return_value = _response(status=429, text="slow down")
        with self.assertRaises(AIQuotaError):
            self.provider.generate("system", "user")

    def test_generate_bad_shape(self):
        self.requests.post.return_value = _response(payload={"unexpected": True})
        with self.assertRaises(AIProviderError):
            self.provider.generate("system", "user")

    def test_generate_network_error(self):
        self.requests.post.side_effect = requests.ConnectionError()
        with self.assertRaises(AINetworkError):
            self.provider.generate("system", "user")

    def test_ping(self):
        getattr(self.requests, self.ping_method).return_value = _response(
            payload=self.ping_payload)
        self.assertTrue(self.provider.ping().startswith("OK"))

    def test_ping_errors(self):
        method = getattr(self.requests, self.ping_method)
        method.return_value = _response(status=401, text="bad key")
        with self.assertRaises(AIAuthError):
            self.provider.ping()
        method.return_value = None
        method.side_effect = requests.Timeout()
        with self.assertRaises(AINetworkError):
            self.provider.ping()

    def test_list_models(self):
        self.requests.get.return_value = _response(payload=self.list_payload)
        self.assertEqual(self.provider.list_models(), self.list_expected)

    def test_list_models_errors(self):
        self.requests.get.return_value = _response(status=404, text="nope")
        with self.assertRaises(AINotFoundError):
            self.provider.list_models()
        self.requests.get.side_effect = requests.ConnectionError()
        with self.assertRaises(AINetworkError):
            self.provider.list_models()


@tagged("post_install", "-at_install")
class TestGeminiProvider(AdapterMixin, TransactionCase):
    code = "gemini"
    cls = GeminiProvider
    generate_payload = {
        "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
        "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 7},
    }
    generate_usage = {"input": 5, "output": 7, "total": 12}
    ping_payload = {"totalTokens": 1}
    list_payload = {"models": [
        {"name": "models/gemini-2.5-flash",
         "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/text-embedding-004",
         "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/gemini-aqa", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/imagen", "supportedGenerationMethods": ["predict"]},
        {"name": ""},
    ]}
    list_expected = ["gemini-2.5-flash"]


@tagged("post_install", "-at_install")
class TestClaudeProvider(AdapterMixin, TransactionCase):
    code = "claude"
    cls = ClaudeProvider
    generate_payload = {
        "content": [{"text": "{}"}],
        "usage": {"input_tokens": 3, "output_tokens": 4},
    }
    generate_usage = {"input": 3, "output": 4, "total": 7}
    ping_payload = {"content": [{"text": "OK"}]}
    list_payload = {"data": [{"id": "claude-sonnet-4-5"}, {"id": "claude-haiku-4-5"},
                             {"id": "claude-sonnet-4-5"}, {"id": ""}]}
    list_expected = ["claude-haiku-4-5", "claude-sonnet-4-5"]

    def test_ping_unexpected_shape(self):
        self.requests.post.return_value = _response(payload={})
        self.assertEqual(self.provider.ping(), "OK")


@tagged("post_install", "-at_install")
class TestOpenAIProvider(AdapterMixin, TransactionCase):
    code = "openai"
    cls = OpenAIProvider
    generate_payload = {
        "choices": [{"message": {"content": "{}"}}],
        "usage": {"prompt_tokens": 2, "completion_tokens": 3},
    }
    generate_usage = {"input": 2, "output": 3, "total": 5}
    ping_method = "get"
    ping_payload = {"data": [{"id": "gpt-4o"}]}
    list_payload = {"data": [
        {"id": "gpt-4o"}, {"id": "gpt-4o-2024-08-06"}, {"id": "o3-mini"},
        {"id": "text-embedding-3-small"}, {"id": "gpt-4o-audio-preview"},
        {"id": "dall-e-3"}, {"id": ""},
    ]}
    list_expected = ["gpt-4o", "o3-mini"]

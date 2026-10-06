# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
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
################################################################################

from abc import ABC, abstractmethod


# ── Typed errors so callers can show friendly messages ────────────────────

class AIProviderError(Exception):
    """Base class for any provider-side failure."""


class AIQuotaError(AIProviderError):
    """Rate limit or quota exceeded (HTTP 429)."""


class AIAuthError(AIProviderError):
    """Invalid / missing / revoked API key (HTTP 401 or 403)."""


class AINotFoundError(AIProviderError):
    """Requested model or endpoint doesn't exist (HTTP 404)."""


class AINetworkError(AIProviderError):
    """Network-level failure (timeout, DNS, connection refused)."""


def classify_http_error(status_code, body_snippet):
    """Map an HTTP status code to the right typed AIProviderError subclass."""
    if status_code == 429:
        return AIQuotaError(
            "Rate limit or quota exceeded. "
            "Free tiers usually allow ~15 requests/minute and a daily token cap. "
            "Wait a minute and try again, or switch to a different model "
            "(gemini-1.5-flash has a more generous free quota). "
            "Raw response: " + body_snippet
        )
    if status_code in (401, 403):
        return AIAuthError(
            "Authentication failed (HTTP %d). "
            "Your API key may be invalid, revoked, or restricted "
            "(check the key's allowed referrers/IPs in Google AI Studio). "
            "Raw response: %s" % (status_code, body_snippet)
        )
    if status_code == 404:
        return AINotFoundError(
            "Model or endpoint not found (HTTP 404). "
            "The model name may be wrong or not available in your region. "
            "Raw response: " + body_snippet
        )
    return AIProviderError(
        "Provider returned HTTP %d: %s" % (status_code, body_snippet)
    )


# ── Usage helper ──────────────────────────────────────────────────────────

def empty_usage():
    """A zeroed-out usage dict used as a fallback when a provider response
    doesn't include usage metadata (rare but possible)."""
    return {"input": 0, "output": 0, "total": 0}


# ── Abstract base ─────────────────────────────────────────────────────────

class AIProviderBase(ABC):
    code = None  # subclasses set this to "gemini" / "claude" / "openai"

    def __init__(self, api_key, model, base_url):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    @abstractmethod
    def generate(self, system_prompt, user_prompt):
        """Send the prompts to the provider.

        Returns: tuple (text, usage)
            text  -- the model's raw text response
            usage -- {"input": int, "output": int, "total": int}
        """
        raise NotImplementedError

    def ping(self):
        """Lightweight connectivity check. Returns a short status string."""
        text, _usage = self.generate(
            system_prompt="Reply with exactly: OK",
            user_prompt="ping",
        )
        return text

    def list_models(self):
        """Return a sorted list of generation-capable model IDs the API key
        can currently access.

        Each adapter implements this differently — Gemini, Claude, and OpenAI
        all have different /models response shapes and filter rules.
        """
        raise NotImplementedError(
            "Provider %r does not support list_models" % (self.code,)
        )


# ── Factory ───────────────────────────────────────────────────────────────

def get_provider(code, api_key, model, base_url):
    from .provider_gemini import GeminiProvider
    from .provider_claude import ClaudeProvider
    from .provider_openai import OpenAIProvider

    mapping = {
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
    }
    if code not in mapping:
        raise AIProviderError("Unknown provider code: %r" % code)
    return mapping[code](api_key=api_key, model=model, base_url=base_url)

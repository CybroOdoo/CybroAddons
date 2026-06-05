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

import logging
import requests

from .provider_base import (
    AIProviderBase,
    AIProviderError,
    AINetworkError,
    classify_http_error,
    empty_usage,
)

_logger = logging.getLogger(__name__)


class GeminiProvider(AIProviderBase):
    """Google Gemini via the Generative Language REST API.

    Endpoints:
      - generateContent: full inference
      - countTokens:     token count (separate quota — used for ping())
    """

    code = "gemini"

    def generate(self, system_prompt, user_prompt):
        url = "%s/models/%s:generateContent?key=%s" % (
            self.base_url, self.model, self.api_key,
        )
        body = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        try:
            resp = requests.post(url, json=body, timeout=120)
        except requests.RequestException as exc:
            raise AINetworkError(
                "Network error reaching Gemini: %s" % type(exc).__name__
            ) from exc

        _logger.info(
            "Gemini generate: status=%s body_length=%s",
            resp.status_code, len(resp.content),
        )

        if resp.status_code != 200:
            raise classify_http_error(resp.status_code, resp.text[:300])

        data = resp.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise AIProviderError(
                "Unexpected Gemini response shape: %s" % exc
            ) from exc

        # Extract token usage from usageMetadata
        usage = empty_usage()
        meta = data.get("usageMetadata") or {}
        usage["input"]  = int(meta.get("promptTokenCount", 0) or 0)
        usage["output"] = int(meta.get("candidatesTokenCount", 0) or 0)
        usage["total"]  = int(meta.get("totalTokenCount", 0) or 0)
        # Some Gemini responses omit totalTokenCount — fall back to sum
        if not usage["total"]:
            usage["total"] = usage["input"] + usage["output"]

        return text, usage

    def ping(self):
        """Use countTokens — separate quota from generateContent."""
        url = "%s/models/%s:countTokens?key=%s" % (
            self.base_url, self.model, self.api_key,
        )
        body = {"contents": [{"role": "user", "parts": [{"text": "ping"}]}]}
        try:
            resp = requests.post(url, json=body, timeout=30)
        except requests.RequestException as exc:
            raise AINetworkError(
                "Network error reaching Gemini: %s" % type(exc).__name__
            ) from exc
        _logger.info("Gemini ping (countTokens): status=%s", resp.status_code)
        if resp.status_code != 200:
            raise classify_http_error(resp.status_code, resp.text[:300])
        data = resp.json()
        total = data.get("totalTokens", "?")
        return "OK — countTokens returned %s tokens" % total

    def list_models(self):
        """List Gemini models that can be used for text generation.

        Filters out embedding, vision-only, and tuning models — keeps only
        the ones that support the generateContent action.
        """
        url = "%s/models?key=%s" % (self.base_url, self.api_key)
        try:
            resp = requests.get(url, timeout=30)
        except requests.RequestException as exc:
            raise AINetworkError(
                "Network error reaching Gemini: %s" % type(exc).__name__
            ) from exc

        _logger.info("Gemini list_models: status=%s", resp.status_code)
        if resp.status_code != 200:
            raise classify_http_error(resp.status_code, resp.text[:300])

        data = resp.json()
        models = []
        for m in data.get("models", []) or []:
            # Gemini returns names like "models/gemini-2.5-flash" — strip the prefix
            name = (m.get("name") or "").replace("models/", "", 1)
            if not name:
                continue
            # Only include models that support generateContent
            methods = m.get("supportedGenerationMethods") or []
            if "generateContent" not in methods:
                continue
            # Skip embedding and aqa specialised models
            if "embedding" in name or name.endswith("-aqa"):
                continue
            models.append(name)
        return sorted(set(models))

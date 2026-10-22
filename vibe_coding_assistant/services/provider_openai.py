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


class OpenAIProvider(AIProviderBase):
    """OpenAI Chat Completions REST API."""

    code = "openai"

    @staticmethod
    def _is_reasoning_model(model):
        """True for the o-series reasoning models (o1, o1-mini, o3, o3-mini,
        o4-mini, …).

        These models differ from the gpt-* chat models in three ways that
        break the standard request body:
          - they reject any `temperature` other than the default (1);
          - the older snapshots (o1-mini, o1-preview) reject the `system`
            role and `response_format`.
        We detect them by the leading "o<digit>" pattern.
        """
        m = (model or "").lower()
        return len(m) >= 2 and m[0] == "o" and m[1].isdigit()

    def generate(self, system_prompt, user_prompt):
        url = "%s/chat/completions" % self.base_url
        headers = {
            "Authorization": "Bearer %s" % self.api_key,
            "content-type": "application/json",
        }

        if self._is_reasoning_model(self.model):
            # Reasoning models: no custom temperature, no response_format, and
            # no system role (unsupported on older o-series snapshots). Fold
            # the system prompt into the user message — the prompt itself
            # already enforces JSON-only output, and the response parser is
            # tolerant of stray formatting.
            body = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": "%s\n\n%s" % (system_prompt, user_prompt),
                    },
                ],
            }
        else:
            body = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            }

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=120)
        except requests.RequestException as exc:
            raise AINetworkError(
                "Network error reaching OpenAI: %s" % type(exc).__name__
            ) from exc

        _logger.info(
            "OpenAI response: status=%s body_length=%s",
            resp.status_code, len(resp.content),
        )

        if resp.status_code != 200:
            raise classify_http_error(resp.status_code, resp.text[:300])

        data = resp.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise AIProviderError(
                "Unexpected OpenAI response shape: %s" % exc
            ) from exc

        # OpenAI usage shape: {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}
        usage = empty_usage()
        meta = data.get("usage") or {}
        usage["input"]  = int(meta.get("prompt_tokens", 0) or 0)
        usage["output"] = int(meta.get("completion_tokens", 0) or 0)
        usage["total"]  = int(meta.get("total_tokens", 0) or 0)
        if not usage["total"]:
            usage["total"] = usage["input"] + usage["output"]

        return text, usage

    def ping(self):
        url = "%s/models" % self.base_url
        headers = {"Authorization": "Bearer %s" % self.api_key}
        try:
            resp = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as exc:
            raise AINetworkError(
                "Network error reaching OpenAI: %s" % type(exc).__name__
            ) from exc
        _logger.info("OpenAI ping: status=%s", resp.status_code)
        if resp.status_code != 200:
            raise classify_http_error(resp.status_code, resp.text[:300])
        data = resp.json()
        count = len(data.get("data", []))
        return "OK — %d models accessible" % count

    def list_models(self):
        """List OpenAI chat-capable models accessible to this key.

        OpenAI's /models endpoint returns everything (including embeddings,
        DALL-E, Whisper, etc.). We filter for chat-completion-capable
        models by name pattern — the API doesn't expose a "capabilities"
        field reliably across model generations.
        """
        import re

        url = "%s/models" % self.base_url
        headers = {"Authorization": "Bearer %s" % self.api_key}
        try:
            resp = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as exc:
            raise AINetworkError(
                "Network error reaching OpenAI: %s" % type(exc).__name__
            ) from exc

        _logger.info("OpenAI list_models: status=%s", resp.status_code)
        if resp.status_code != 200:
            raise classify_http_error(resp.status_code, resp.text[:300])

        data = resp.json()
        models = []
        # Prefixes for chat-completion-capable model families
        chat_prefixes = ("gpt-", "o1", "o3", "o4", "chatgpt-")
        # Excluded patterns (audio, image, embeddings, fine-tuned snapshots)
        exclude_substrings = (
            "embedding", "whisper", "tts", "dall-e", "davinci",
            "babbage", "ada-", "audio", "image", "vision-preview",
            "moderation", "search", "transcribe", "realtime",
        )
        # Dated snapshots — match common patterns OpenAI uses:
        #   gpt-4o-2024-08-06        (YYYY-MM-DD)
        #   gpt-4-turbo-2024-04-09   (YYYY-MM-DD)
        #   gpt-3.5-turbo-0613       (MMDD, 4 trailing digits)
        #   gpt-3.5-turbo-16k-0613   (MMDD with size mid-id)
        # We keep the latest aliases (gpt-4o, gpt-3.5-turbo) only.
        dated_pattern = re.compile(
            r"-(?:\d{4}-\d{2}-\d{2}|\d{4})(?:$|-)"
        )

        for m in data.get("data", []) or []:
            mid = m.get("id") or ""
            if not mid:
                continue
            if not mid.startswith(chat_prefixes):
                continue
            if any(s in mid for s in exclude_substrings):
                continue
            if dated_pattern.search(mid):
                continue
            models.append(mid)
        return sorted(set(models))

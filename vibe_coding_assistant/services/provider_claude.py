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


class ClaudeProvider(AIProviderBase):
    """Anthropic Claude via the Messages REST API."""

    code = "claude"

    def generate(self, system_prompt, user_prompt):
        url = "%s/messages" % self.base_url
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": 8192,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=120)
        except requests.RequestException as exc:
            raise AINetworkError(
                "Network error reaching Claude: %s" % type(exc).__name__
            ) from exc

        _logger.info(
            "Claude response: status=%s body_length=%s",
            resp.status_code, len(resp.content),
        )

        if resp.status_code != 200:
            raise classify_http_error(resp.status_code, resp.text[:300])

        data = resp.json()
        try:
            text = data["content"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise AIProviderError(
                "Unexpected Claude response shape: %s" % exc
            ) from exc

        # Anthropic's usage shape: {"input_tokens": N, "output_tokens": N}
        usage = empty_usage()
        meta = data.get("usage") or {}
        usage["input"]  = int(meta.get("input_tokens", 0) or 0)
        usage["output"] = int(meta.get("output_tokens", 0) or 0)
        usage["total"]  = usage["input"] + usage["output"]

        return text, usage

    def ping(self):
        url = "%s/messages" % self.base_url
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Reply OK"}],
        }
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=30)
        except requests.RequestException as exc:
            raise AINetworkError(
                "Network error reaching Claude: %s" % type(exc).__name__
            ) from exc
        _logger.info("Claude ping: status=%s", resp.status_code)
        if resp.status_code != 200:
            raise classify_http_error(resp.status_code, resp.text[:300])
        data = resp.json()
        try:
            return "OK — replied: %s" % data["content"][0]["text"][:40]
        except (KeyError, IndexError):
            return "OK"

    def list_models(self):
        """List Claude models accessible via the /models endpoint.

        Anthropic's /models endpoint returns the catalog. All entries are
        chat-capable; no filtering needed beyond extracting the IDs.
        """
        url = "%s/models" % self.base_url
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as exc:
            raise AINetworkError(
                "Network error reaching Claude: %s" % type(exc).__name__
            ) from exc

        _logger.info("Claude list_models: status=%s", resp.status_code)
        if resp.status_code != 200:
            raise classify_http_error(resp.status_code, resp.text[:300])

        data = resp.json()
        models = []
        for m in data.get("data", []) or []:
            mid = m.get("id") or ""
            if mid:
                models.append(mid)
        return sorted(set(models))

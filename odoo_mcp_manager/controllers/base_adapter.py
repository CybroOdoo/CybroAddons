# -*- coding: utf-8 -*-
"""Base adapter contract for all platform adapters."""

from abc import ABC, abstractmethod


class BasePlatformAdapter(ABC):
    """
    Every platform adapter must implement normalize() and format_response().
    Optionally override send_reply() to push the reply directly via the
    platform's API instead of relying on the inline webhook response.

    BotMessage schema (canonical unified format):
    {
        "platform":         str,   # telegram | whatsapp | web
        "platform_user_id": str,   # unique user ID on that platform
        "text":             str,   # plain user text
        "attachments":      list,  # list of media URLs (may be empty)
        "metadata":         dict,  # platform-specific passthrough data
    }

    Response schema (from BotGatewayService):
    {
        "text":     str,   # reply text produced by MCP
        "metadata": dict,  # merged routing + platform metadata
    }
    """

    @abstractmethod
    def normalize(self, raw_payload: dict) -> dict:
        """Convert raw platform webhook payload → unified BotMessage dict."""

    @abstractmethod
    def format_response(self, response: dict) -> dict:
        """Convert unified response dict → platform-specific reply payload."""

    def send_reply(self, _channel, _response: dict) -> bool:
        """
        Push the reply directly via the platform's own API.

        Args:
            channel: ai.bot.channel record (holds credentials / tokens).
            response: unified response dict with 'text' and 'metadata'.

        Returns:
            True  — message was sent; controller should return 200 OK.
            False — not handled here; controller falls back to inline response.
        """
        return False

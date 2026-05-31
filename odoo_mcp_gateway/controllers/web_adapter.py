# -*- coding: utf-8 -*-
"""Web Chat adapter for the embedded Odoo web chat widget."""

from .base_adapter import BasePlatformAdapter


class WebAdapter(BasePlatformAdapter):
    """
    Handles requests from the embedded JavaScript web-chat widget.
    Expects a simple JSON body:
        {
            "session_id": "browser-session-or-user-uuid",
            "message":    "user text",
            "attachments": [],        # optional
            "metadata": {}            # optional passthrough
        }
    """

    def normalize(self, raw: dict) -> dict:
        return {
            'platform':         'web',
            'platform_user_id': raw.get('session_id') or 'anonymous',
            'text':             raw.get('message', ''),
            'attachments':      raw.get('attachments', []),
            'metadata':         raw.get('metadata', {}),
        }

    def format_response(self, response: dict) -> dict:
        return {
            'reply':     response.get('text', ''),
            'tool_used': response.get('metadata', {}).get('tool'),
            'session_id': response.get('metadata', {}).get('platform_user_id', ''),
        }

# -*- coding: utf-8 -*-
"""WhatsApp Cloud API adapter (Meta / 360Dialog compatible)."""

import logging
import requests
from .base_adapter import BasePlatformAdapter

_logger = logging.getLogger(__name__)
_GRAPH_API_VERSION = 'v19.0'


class WhatsAppAdapter(BasePlatformAdapter):
    """
    Normalises WhatsApp Cloud API webhook payloads and sends replies via
    the Meta Graph API ``/messages`` endpoint.

    Supports text messages and interactive button replies.  Media attachments
    are extracted as WhatsApp media IDs.
    """

    MAX_TEXT_LEN = 4096

    def normalize(self, raw: dict) -> dict:
        """Convert a WhatsApp webhook payload to the unified BotMessage format."""
        try:
            entry = (raw.get('entry') or [{}])[0]
            changes = (entry.get('changes') or [{}])[0]
            value = changes.get('value') or {}
            msg = (value.get('messages') or [{}])[0]
            meta = value.get('metadata') or {}
        except (IndexError, AttributeError):
            msg, meta = {}, {}
        text = (
            (msg.get('text') or {}).get('body', '')
            or (msg.get('interactive') or {}).get('button_reply', {}).get('title', '')
            or ''
        )
        attachments = [
            media['id']
            for media_type in ('image', 'document', 'audio', 'video', 'sticker')
            for media in [msg.get(media_type) or {}]
            if media.get('id')
        ]
        return {
            'platform': 'whatsapp',
            'platform_user_id': msg.get('from', ''),
            'text': text,
            'attachments': attachments,
            'metadata': {
                'phone_number_id': meta.get('phone_number_id', ''),
                'display_phone': meta.get('display_phone_number', ''),
                'message_id': msg.get('id', ''),
                'wa_id': msg.get('from', ''),
                'message_type': msg.get('type', 'text'),
            },
        }

    def format_response(self, response: dict) -> dict:
        """Convert a unified response to a WhatsApp Cloud API message payload."""
        text = response.get('text', '')
        if len(text) > self.MAX_TEXT_LEN:
            text = text[:self.MAX_TEXT_LEN - 3] + '...'
        meta = response.get('metadata', {})
        return {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': meta.get('wa_id') or meta.get('platform_user_id', ''),
            'type': 'text',
            'text': {'body': text},
        }

    def send_reply(self, channel, response: dict) -> bool:
        """
        Send reply via the WhatsApp Cloud API (graph.facebook.com).

        Returns:
            True when the message was delivered, False otherwise.
        """
        token = (channel.api_token or '').strip() if channel else ''
        phone_id = (channel.whatsapp_phone_id or '').strip() if channel else ''
        meta = response.get('metadata', {})
        to = meta.get('wa_id') or meta.get('platform_user_id', '')
        text = response.get('text', '')

        if not token or not phone_id or not to or not text:
            _logger.warning(
                'WhatsAppAdapter.send_reply: missing credentials or recipient — '
                'token=%s phone_id=%s to=%s',
                bool(token), bool(phone_id), bool(to),
            )
            return False

        if len(text) > self.MAX_TEXT_LEN:
            text = text[:self.MAX_TEXT_LEN - 3] + '...'

        try:
            resp = requests.post(
                f'https://graph.facebook.com/{_GRAPH_API_VERSION}/{phone_id}/messages',
                json={
                    'messaging_product': 'whatsapp',
                    'recipient_type': 'individual',
                    'to': to,
                    'type': 'text',
                    'text': {'body': text},
                },
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                timeout=10,
            )
            data = resp.json()
            if data.get('messages'):
                return True
            _logger.error('WhatsAppAdapter: send failed — %s', data)
            return False
        except requests.exceptions.RequestException as exc:
            _logger.error('WhatsAppAdapter: network error — %s', exc)
            return False

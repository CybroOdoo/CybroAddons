# -*- coding: utf-8 -*-
"""Telegram platform adapter."""

import logging
import requests
from .base_adapter import BasePlatformAdapter

_logger = logging.getLogger(__name__)


class TelegramAdapter(BasePlatformAdapter):
    """
    Normalises Telegram Bot API webhook payloads and sends replies via
    the ``sendMessage`` endpoint.

    Handles regular messages, edited messages, and callback queries.
    Attempts Markdown formatting first, then retries as plain text on a
    parse error (error_code 400).
    """

    MAX_TEXT_LEN = 4096

    def normalize(self, raw: dict) -> dict:
        """Convert a Telegram update payload to the unified BotMessage format."""
        msg = (
            raw.get('message')
            or raw.get('edited_message')
            or raw.get('callback_query', {}).get('message', {})
        ) or {}
        from_data = msg.get('from') or {}
        chat_data = msg.get('chat') or {}
        text = (
            msg.get('text')
            or raw.get('callback_query', {}).get('data', '')
            or ''
        )
        return {
            'platform': 'telegram',
            'platform_user_id': str(from_data.get('id', '')),
            'text': text,
            'attachments': self._extract_attachments(msg),
            'metadata': {
                'chat_id': str(chat_data.get('id', '')),
                'username': from_data.get('username', ''),
                'update_id': raw.get('update_id'),
                'message_id': msg.get('message_id'),
            },
        }

    def format_response(self, response: dict) -> dict:
        """Convert a unified response to a Telegram sendMessage payload."""
        text = response.get('text', '')
        if len(text) > self.MAX_TEXT_LEN:
            text = text[:self.MAX_TEXT_LEN - 3] + '...'
        return {
            'method': 'sendMessage',
            'chat_id': response.get('metadata', {}).get('chat_id', ''),
            'text': text,
        }

    def send_reply(self, channel, response: dict) -> bool:
        """
        Push the reply directly to Telegram via the Bot API.

        Tries Markdown first; retries as plain text when Telegram returns a
        400 parse error.

        Returns:
            True when the message was delivered, False otherwise.
        """
        token = (channel.api_token or '').strip() if channel else ''
        chat_id = response.get('metadata', {}).get('chat_id', '')
        text = response.get('text', '')
        if not token or not chat_id or not text:
            _logger.warning('TelegramAdapter.send_reply: missing token, chat_id or text')
            return False
        if len(text) > self.MAX_TEXT_LEN:
            text = text[:self.MAX_TEXT_LEN - 3] + '...'
        for parse_mode in ('Markdown', None):
            payload = {'chat_id': chat_id, 'text': text}
            if parse_mode:
                payload['parse_mode'] = parse_mode
            try:
                resp = requests.post(
                    f'https://api.telegram.org/bot{token}/sendMessage',
                    json=payload,
                    timeout=10,
                )
                data = resp.json()
                if data.get('ok'):
                    return True
                if data.get('error_code') == 400 and parse_mode:
                    _logger.warning(
                        'TelegramAdapter: Markdown error, retrying plain — %s',
                        data.get('description'),
                    )
                    continue
                _logger.error(
                    'TelegramAdapter: sendMessage failed — %s', data.get('description')
                )
                return False
            except requests.exceptions.RequestException as exc:
                _logger.error('TelegramAdapter: network error — %s', exc)
                return False
        return False

    @staticmethod
    def _extract_attachments(msg: dict) -> list:
        """Extract file_id values from photo and document fields."""
        urls = []
        if msg.get('photo'):
            urls.append(msg['photo'][-1].get('file_id', ''))
        if msg.get('document'):
            urls.append(msg['document'].get('file_id', ''))
        return urls

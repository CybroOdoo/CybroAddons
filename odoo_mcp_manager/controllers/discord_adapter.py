# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
##############################################################################
import logging
import requests
from .base_adapter import BasePlatformAdapter

_logger = logging.getLogger(__name__)

# Discord Interaction type constants
INTERACTION_PING = 1
INTERACTION_APPLICATION_COMMAND = 2
INTERACTION_MESSAGE_COMPONENT = 3

# Discord Interaction callback type
CALLBACK_CHANNEL_MESSAGE = 4          # reply with a message
DISCORD_API_BASE = 'https://discord.com/api/v10'


class DiscordAdapter(BasePlatformAdapter):
    """
    Normalises Discord Interactions webhook payloads and sends replies via
    the Discord REST API.

    Discord requires a fast response (within 3 s for interactions), so
    replies are sent immediately via the Interactions endpoint using the
    interaction token, rather than after a full service round-trip.
    The controller short-circuits PING events before reaching the service.
    """

    MAX_TEXT_LEN = 2000  # Discord message character limit

    # ── normalize ────────────────────────────────────────────────────────────

    def normalize(self, raw: dict) -> dict:
        """Convert a Discord Interaction payload to the unified BotMessage format."""
        interaction_type = raw.get('type', 0)
        user_data = (
            raw.get('member', {}).get('user')
            or raw.get('user')
            or {}
        )
        guild_id = raw.get('guild_id', '')
        channel_id = raw.get('channel_id', '')

        # Extract text from slash command options or resolved message
        text = ''
        data = raw.get('data', {})
        options = data.get('options', [])
        if options:
            # Grab the first string option value (covers /ask <prompt> pattern)
            text = next(
                (str(opt.get('value', '')) for opt in options if opt.get('value')),
                '',
            )
        if not text:
            # Fallback: resolved message content (message components)
            text = (
                raw.get('message', {}).get('content', '')
                or data.get('custom_id', '')
            )

        return {
            'platform': 'discord',
            'platform_user_id': str(user_data.get('id', '')),
            'text': text,
            'attachments': [],
            'metadata': {
                'guild_id': str(guild_id),
                'channel_id': str(channel_id),
                'interaction_id': str(raw.get('id', '')),
                'interaction_token': raw.get('token', ''),
                'application_id': str(raw.get('application_id', '')),
                'username': user_data.get('username', ''),
                'interaction_type': interaction_type,
                'command_name': data.get('name', ''),
            },
        }

    # ── format_response ──────────────────────────────────────────────────────

    def format_response(self, response: dict) -> dict:
        """Convert a unified response to a Discord Interactions response payload."""
        text = response.get('text', '') or '(no response)'
        if len(text) > self.MAX_TEXT_LEN:
            text = text[:self.MAX_TEXT_LEN - 3] + '...'
        return {
            'type': CALLBACK_CHANNEL_MESSAGE,
            'data': {'content': text},
        }

    # ── send_reply ───────────────────────────────────────────────────────────

    def send_reply(self, channel, response: dict) -> bool:
        """
        Send the reply via Discord's Interactions follow-up endpoint.

        Discord grants a 15-minute window to reply using the interaction token,
        so we send a follow-up message rather than the initial 3-second response
        (which is handled inline by the controller returning the JSON payload).

        Returns:
            True  — follow-up was posted successfully.
            False — caller should fall back to inline response body.
        """
        token = (channel.api_token or '').strip() if channel else ''
        metadata = response.get('metadata', {})
        application_id = metadata.get('application_id', '')
        interaction_token = metadata.get('interaction_token', '')
        text = response.get('text', '') or '(no response)'

        if not token or not application_id or not interaction_token:
            _logger.warning(
                'DiscordAdapter.send_reply: missing bot_token, application_id or '
                'interaction_token — falling back to inline response'
            )
            return False

        if len(text) > self.MAX_TEXT_LEN:
            text = text[:self.MAX_TEXT_LEN - 3] + '...'

        url = f'{DISCORD_API_BASE}/webhooks/{application_id}/{interaction_token}'
        headers = {
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/json',
        }
        try:
            resp = requests.post(
                url,
                headers=headers,
                json={'content': text},
                timeout=10,
            )
            if resp.status_code in (200, 204):
                return True
            _logger.error(
                'DiscordAdapter.send_reply: HTTP %s — %s',
                resp.status_code, resp.text,
            )
        except requests.exceptions.RequestException as exc:
            _logger.error('DiscordAdapter.send_reply: network error — %s', exc)
        return False

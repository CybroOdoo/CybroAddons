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
import json
import logging
from odoo import http
from odoo.http import request
from .telegram_adapter import TelegramAdapter
from .web_adapter import WebAdapter
from .whatsapp_adapter import WhatsAppAdapter
from .discord_adapter import DiscordAdapter
from ..services.bot_gateway_service import BotGatewayService
from ..utils.bot_auth import check_rate_limit, validate_bot_api_key

_logger = logging.getLogger(__name__)

_ADAPTERS = {
    'telegram': TelegramAdapter(),
    'whatsapp': WhatsAppAdapter(),
    'web': WebAdapter(),
    'discord': DiscordAdapter(),
}


class BotGatewayController(http.Controller):
    """Universal webhook controller for the Bot Integration Layer."""

    # ── Public platform routes ────────────────────────────────────────────────

    @http.route('/bot/telegram', type='http', auth='public', methods=['POST'], csrf=False)
    def telegram(self, **kw) -> object:
        """Receive and process Telegram Bot API webhook updates."""
        return self._handle('telegram')

    @http.route('/bot/whatsapp', type='http', auth='public', methods=['POST'], csrf=False)
    def whatsapp(self, **kw) -> object:
        """Receive and process WhatsApp Cloud API webhook updates."""
        return self._handle('whatsapp')

    @http.route('/bot/whatsapp/verify', type='http', auth='public', methods=['GET'], csrf=False)
    def whatsapp_verify(self, **kw) -> object:
        """Handle the WhatsApp webhook hub challenge verification handshake."""
        hub_mode = request.httprequest.args.get('hub.mode')
        hub_challenge = request.httprequest.args.get('hub.challenge')
        hub_verify = request.httprequest.args.get('hub.verify_token')
        expected = request.env['ir.config_parameter'].sudo().get_param(
            'bot_gateway.webhook_secret', ''
        )
        if hub_mode == 'subscribe' and hub_verify == expected:
            _logger.info('BotGateway: WhatsApp webhook verified successfully')
            return request.make_response(
                hub_challenge or '', headers=[('Content-Type', 'text/plain')]
            )
        return self._json({'error': 'Forbidden'}, status=403)

    @http.route('/bot/web', type='http', auth='public', methods=['POST'], csrf=False)
    def web(self, **kw) -> object:
        """Receive and process web chat widget messages."""
        return self._handle('web')

    @http.route('/bot/discord', type='http', auth='public', methods=['POST'], csrf=False)
    def discord(self, **kw) -> object:
        """
        Receive Discord Interactions webhook events.

        Discord requires a response within 3 seconds. Since AI processing
        takes longer, we immediately return type-5 (DEFERRED) to show
        "App is thinking..." in Discord, then process the message in a
        background thread and send the real reply via the follow-up webhook.

        Flow:
          1. Verify Ed25519 signature → 401 if invalid.
          2. PING (type=1) → return {type: 1} immediately.
          3. All other interactions → return {type: 5} (DEFERRED) immediately.
          4. Background thread processes message and POSTs follow-up reply.
        """
        import json as _json
        import threading

        body_bytes = request.httprequest.data or b''
        signature = request.httprequest.headers.get('X-Signature-Ed25519', '')
        timestamp = request.httprequest.headers.get('X-Signature-Timestamp', '')

        # Fetch the Discord channel's public key for signature verification
        channel = request.env['ai.bot.channel'].sudo().search(
            [('platform', '=', 'discord'), ('status', '=', 'active')], limit=1
        )
        if not channel:
            channel = request.env['ai.bot.channel'].sudo().search(
                [('platform', '=', 'discord')], limit=1
            )

        public_key_hex = (channel.discord_public_key or '').strip() if channel else ''

        if not public_key_hex:
            _logger.warning(
                'BotGateway Discord: no Public Key configured — '
                'add it from Discord Developer Portal → General Information → Public Key'
            )
            return self._json({'error': 'Discord Public Key not configured'}, status=401)

        if not signature or not timestamp:
            _logger.warning('BotGateway Discord: missing signature headers')
            return self._json({'error': 'Missing signature headers'}, status=401)

        if not self._verify_discord_signature(public_key_hex, signature, timestamp, body_bytes):
            _logger.warning('BotGateway Discord: invalid Ed25519 signature — rejected')
            return self._json({'error': 'Invalid request signature'}, status=401)

        try:
            raw = _json.loads(body_bytes or b'{}')
        except _json.JSONDecodeError:
            return self._json({'error': 'Invalid JSON body'}, status=400)

        # Acknowledge Discord ownership PING immediately
        if raw.get('type') == 1:
            _logger.info('BotGateway: Discord PING verified and acknowledged')
            return self._json({'type': 1})

        # Normalize the payload now (on the main thread while env is available)
        adapter = _ADAPTERS['discord']
        bot_message = adapter.normalize(raw)

        # Resolve the active bot channel
        bot_message.setdefault('metadata', {})['bot_channel_id'] = channel.id if channel else False

        # Capture everything needed for the background thread
        application_id = bot_message['metadata'].get('application_id', '')
        interaction_token = bot_message['metadata'].get('interaction_token', '')
        bot_token = (channel.api_token or '').strip() if channel else ''
        env = request.env

        def _process_and_reply():
            """Process the Discord interaction and send the follow-up reply."""
            from ..services.bot_gateway_service import BotGatewayService
            import requests as _req
            try:
                with env.registry.cursor() as new_cr:
                    new_env = env(cr=new_cr)
                    response = BotGatewayService(new_env).process(bot_message)
                    text = (response.get('text') or '(no response)')[:2000]
            except Exception:
                _logger.exception('BotGateway Discord: background processing failed')
                text = 'Sorry, something went wrong. Please try again.'

            # Send follow-up reply via Discord webhook
            followup_url = (
                f'https://discord.com/api/v10/webhooks/{application_id}/{interaction_token}'
            )
            try:
                resp = _req.post(
                    followup_url,
                    json={'content': text},
                    timeout=15,
                )
                if resp.status_code not in (200, 204):
                    _logger.error(
                        'BotGateway Discord follow-up failed: HTTP %s — %s',
                        resp.status_code, resp.text,
                    )
                else:
                    _logger.info('BotGateway Discord: follow-up reply sent successfully')
            except Exception as exc:
                _logger.error('BotGateway Discord: follow-up network error — %s', exc)

        # Spawn background thread and immediately return DEFERRED to Discord
        threading.Thread(target=_process_and_reply, daemon=True).start()

        # Type 5 = DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
        # Discord shows "App is thinking..." until the follow-up arrives
        return self._json({'type': 5})

    @staticmethod
    def _verify_discord_signature(
        public_key_hex: str, signature_hex: str, timestamp: str, body: bytes
    ) -> bool:
        """Verify a Discord Ed25519 request signature."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from cryptography.exceptions import InvalidSignature
            import binascii

            pub_key_bytes = binascii.unhexlify(public_key_hex)
            sig_bytes = binascii.unhexlify(signature_hex)
            message = timestamp.encode() + body

            public_key = Ed25519PublicKey.from_public_bytes(pub_key_bytes)
            public_key.verify(sig_bytes, message)
            return True
        except (InvalidSignature, Exception) as e:
            _logger.debug('Discord sig verification failed: %s', e)
            return False

    @http.route('/bot/health', type='http', auth='none', methods=['GET'], csrf=False)
    def health(self, **kw) -> object:
        """Public health-check endpoint; returns platform list and status."""
        return self._json({
            'status': 'ok',
            'gateway': 'Bot Integration Layer',
            'platforms': list(_ADAPTERS.keys()),
        })

    def _handle(self, platform: str, raw: dict = None) -> object:
        """
        Shared pipeline for all platform POST routes.

        Steps: rate-limit → auth → parse body → normalize →
               service call → format → send reply.
        """
        ip = request.httprequest.remote_addr

        if not check_rate_limit(ip):
            _logger.warning('BotGateway: rate limit hit from %s', ip)
            return self._json({'error': 'Too many requests'}, status=429)

        key = (
            request.httprequest.headers.get('X-Bot-Secret')
            or request.httprequest.args.get('secret', '')
        )
        if not validate_bot_api_key(request.env, key):
            return self._json({'error': 'Unauthorized'}, status=401)

        if raw is None:
            try:
                raw = json.loads(request.httprequest.data or b'{}')
            except json.JSONDecodeError:
                return self._json({'error': 'Invalid JSON body'}, status=400)

        adapter = _ADAPTERS[platform]
        bot_message = adapter.normalize(raw)

        # Resolve the active bot channel BEFORE calling process() so the
        # conversation record can be linked to it by name.
        channel = request.env['ai.bot.channel'].sudo().search(
            [('platform', '=', platform), ('status', '=', 'active')], limit=1
        )
        bot_message.setdefault('metadata', {})['bot_channel_id'] = channel.id if channel else False

        _logger.info(
            'BotGateway: %s | bot=%s | user=%s | text=%.80s',
            platform,
            channel.name if channel else '(none)',
            bot_message.get('platform_user_id'),
            bot_message.get('text'),
        )
        try:
            response = BotGatewayService(request.env).process(bot_message)
        except Exception:
            _logger.exception('BotGateway: unhandled error in service layer')
            response = {
                'text': 'Sorry, something went wrong. Please try again.',
                'metadata': {'tool': None},
            }
        response.setdefault('metadata', {}).update({
            **bot_message.get('metadata', {}),
            'platform': platform,
            'platform_user_id': bot_message.get('platform_user_id', ''),
        })
        if adapter.send_reply(channel, response):
            return self._json({'ok': True})
        return self._json(adapter.format_response(response))

    @staticmethod
    def _json(data: dict, status: int = 200) -> object:
        """Serialise *data* as a JSON HTTP response."""
        return request.make_response(
            json.dumps(data, ensure_ascii=False),
            headers=[('Content-Type', 'application/json; charset=utf-8')],
            status=status,
        )

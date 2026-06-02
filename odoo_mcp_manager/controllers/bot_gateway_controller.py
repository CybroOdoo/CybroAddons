# -*- coding: utf-8 -*-
"""
Bot Gateway Controller — Odoo HTTP routes for all chat platform webhooks.

Routes:
    POST /bot/telegram         — Telegram Bot API webhook
    POST /bot/whatsapp         — WhatsApp Cloud API webhook
    GET  /bot/whatsapp/verify  — WhatsApp hub challenge verification
    POST /bot/web              — Embedded web chat widget
    GET  /bot/health           — Health check (no auth required)

Security:
    Every POST route validates:
      1. Sliding-window rate limit per IP (bot_auth.check_rate_limit).
      2. X-Bot-Secret header or ?secret= query param matched against
         ir.config_parameter 'bot_gateway.webhook_secret'.
"""

import json
import logging
from odoo import http
from odoo.http import request
from .telegram_adapter import TelegramAdapter
from .web_adapter import WebAdapter
from .whatsapp_adapter import WhatsAppAdapter
from ..services.bot_gateway_service import BotGatewayService
from ..utils.bot_auth import check_rate_limit, validate_bot_api_key

_logger = logging.getLogger(__name__)

# Singleton adapter instances — stateless, safe to share across requests.
_ADAPTERS = {
    'telegram': TelegramAdapter(),
    'whatsapp': WhatsAppAdapter(),
    'web': WebAdapter(),
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

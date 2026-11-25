# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import json
import logging
from odoo import http
from odoo.http import request
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)


class TelegramWebhookController(http.Controller):
    """Controller for handling Telegram webhooks."""

    @http.route(
        '/telegram/webhook',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    def telegram_webhook(self, **kwargs):
        """
        Handle incoming Telegram webhook requests.
        Authenticates the request using the X-Telegram-Bot-Api-Secret-Token header.
        Parses payload, creates incoming message, and updates bot sync timestamp.
        """
        secret = request.httprequest.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if not secret:
            _logger.warning("Telegram webhook rejected: missing secret header")
            return http.Response(
                json.dumps({
                    "ok": False,
                    "error": "Missing secret header"
                }),
                content_type="application/json",
                status=403
            )

        bot = request.env['telegram.bot'].sudo().search(
            [('webhook_secret', '=', secret)],
            limit=1
        )

        if not bot:
            _logger.warning("Telegram webhook rejected: invalid or unknown secret")
            return http.Response(
                json.dumps({
                    "ok": False,
                    "error": "Unauthorized"
                }),
                content_type="application/json",
                status=403
            )

        try:
            payload = None
            if hasattr(request, 'get_json_data'):
                try:
                    payload = request.get_json_data()
                except Exception:
                    payload = None
            if not payload and hasattr(request.httprequest, 'data') and request.httprequest.data:
                payload = json.loads(request.httprequest.data.decode('utf-8'))

            if not payload or not isinstance(payload, dict):
                return http.Response(
                    json.dumps({
                        "ok": False,
                        "error": "Empty or invalid JSON payload"
                    }),
                    content_type="application/json",
                    status=400
                )

            _logger.info("Received Telegram update (update_id: %s)", payload.get("update_id"))

            # Create incoming message record
            request.env['telegram.message'].sudo().create_incoming(
                bot,
                payload
            )
            bot.sudo().write({
                'last_sync': Datetime.now(),
                'last_error_message': False,
                'status': 'active'
            })
            return http.Response(
                json.dumps({
                    "ok": True
                }),
                content_type="application/json",
                status=200
            )
        except Exception as e:
            _logger.exception("Failed processing telegram webhook: %s", str(e))
            bot.sudo().write({
                'last_error_message': str(e),
                'status': 'error'
            })
            return http.Response(
                json.dumps({
                    "ok": False,
                    "error": str(e)
                }),
                content_type="application/json",
                status=500
            )

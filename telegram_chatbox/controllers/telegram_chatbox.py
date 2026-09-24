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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import logging
from odoo import http
from odoo.http import request
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)


class TelegramWebhookController(http.Controller):
    """
    HTTP Controller to handle incoming webhooks from Telegram servers.
    """

    @http.route(
        ['/telegram/webhook/<string:token>'],
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False
    )
    def telegram_webhook(self, token, **kwargs):
        """
       Handle incoming Telegram webhook requests.
       This endpoint receives updates from Telegram, validates the bot token,
       parses the incoming payload, creates a corresponding incoming message
       record, and updates the bot's last synchronization timestamp.
        """
        bot = request.env['telegram.bot'].sudo().search(
            [('token', '=', token)],
            limit=1
        )
        if not bot:
            _logger.warning("Telegram webhook hit with invalid token")
            return http.Response(
                json.dumps({
                    "ok": False,
                    "error": "Invalid bot token"
                }),
                content_type="application/json",
                status=404
            )

        try:
            # Parse Telegram payload
            payload = json.loads(
                request.httprequest.data.decode('utf-8')
            )
            _logger.info("Received Telegram payload: %s", payload)
            # Create incoming message record
            request.env['telegram.message'].sudo().create_incoming(
                bot,
                payload
            )
            # Update last sync time
            bot.sudo().write({
                'last_sync': Datetime.now()
            })
            return http.Response(
                json.dumps({
                    "ok": True
                }),
                content_type="application/json",
                status=200
            )
        except Exception as e:
            _logger.exception(
                "Failed processing telegram webhook: %s",
                str(e)
            )
            return http.Response(
                json.dumps({
                    "ok": False,
                    "error": str(e)
                }),
                content_type="application/json",
                status=500
            )

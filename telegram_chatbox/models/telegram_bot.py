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
import logging
import secrets
import requests
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from requests.exceptions import ConnectionError, Timeout

_logger = logging.getLogger(__name__)


class TelegramBot(models.Model):
    """Model to configure and manage Telegram bots."""
    _name = "telegram.bot"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Telegram Bot"

    name = fields.Char(
        string="Name",
        required=True,
        help="Display name of the Telegram bot configuration."
    )

    token = fields.Char(
        string="API Token",
        required=True,
        tracking=True,
        groups='telegram_chatbox.telegram_group_admin',
        help="Telegram Bot API token obtained from BotFather."
    )

    webhook_url = fields.Char(
        string="Webhook URL",
        tracking=True,
        groups='telegram_chatbox.telegram_group_admin',
        help="Public URL where Telegram sends incoming message updates."
    )

    webhook_secret = fields.Char(
        string="Webhook Secret",
        copy=False,
        groups='telegram_chatbox.telegram_group_admin',
        help="Independent secret token sent in X-Telegram-Bot-Api-Secret-Token header."
    )

    active = fields.Boolean(
        default=True,
        help="Enable or disable this bot configuration."
    )

    last_sync = fields.Datetime(
        string="Last Sync",
        help="Date and time of the last successful communication with Telegram."
    )

    status = fields.Selection(
        [('active', 'Active'), ('error', 'Error'), ('disabled', 'Disabled')],
        default='disabled',
        help="Current status of the Telegram bot connection."
    )

    timeout = fields.Integer(
        string="Timeout (Seconds)",
        default=15,
        help="Maximum time in seconds to wait for a response from the Telegram API."
    )

    last_error_message = fields.Text(
        string="Last Error",
        help="Last error message from webhook operations."
    )


    def action_set_webhook(self, url=None):
        """
            Configure the Telegram webhook for the selected bot(s).
            This method registers a webhook URL with the Telegram Bot API, allowing
            Telegram to send updates directly to the application. Upon successful
            registration, the bot status is updated and a success notification is
            displayed to the user.
        """
        for bot in self:
            token = (bot.token or '').strip()
            if not token:
                raise ValidationError(_("Please configure an API Token first."))

            if not bot.webhook_secret:
                bot.webhook_secret = secrets.token_hex(20)

            webhook = (bot.webhook_url or '').strip().rstrip('/')
            if not webhook:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '').strip().rstrip('/')
                if base_url.startswith('http://'):
                    base_url = base_url.replace('http://', 'https://', 1)
                webhook = base_url

            # Ensure the webhook ends with /telegram/webhook exactly once without token in URL
            endpoint = "/telegram/webhook"
            if not webhook.endswith(endpoint):
                if '/telegram/webhook' in webhook:
                    base = webhook.split('/telegram/webhook')[0].rstrip('/')
                    webhook = f"{base}{endpoint}"
                else:
                    webhook = f"{webhook}{endpoint}"

            bot.webhook_url = webhook

            api = f"https://api.telegram.org/bot{bot.token}/setWebhook"
            payload = {
                "url": webhook,
                "secret_token": bot.webhook_secret,
            }
            try:
                res = requests.post(api, json=payload, timeout=bot.timeout)
                _logger.info("Webhook Response: %s", res.text)

                res.raise_for_status()

                result = res.json()
                bot.last_sync = fields.Datetime.now()
                bot.status = 'active'
                bot.last_error_message = False
                
                if result.get("ok"):
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _("Successful"),
                            'message': _("Webhook registered successfully: %s") % (result.get("description") or "OK"),
                            'type': 'success',
                            'sticky': False,
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    }

            except (ConnectionError, Timeout):
                bot.status = 'error'
                bot.last_error_message = "Could not reach Telegram servers."
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Connection Failed"),
                        'message': _("Could not reach Telegram servers."),
                        'type': 'danger',
                        'sticky': True,
                    }
                }

            except Exception as ex:
                bot.status = 'error'
                err_msg = str(ex)
                if hasattr(ex, 'response') and ex.response is not None:
                    err_msg = f"{err_msg}\nTelegram Response: {ex.response.text}"
                bot.last_error_message = err_msg
                _logger.exception("Webhook setup error: %s", ex)

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Error"),
                        'message': _("Webhook configuration error: %s") % err_msg,
                        'type': 'danger',
                        'sticky': False,
                    }
                }

    @api.model
    def get_by_token(self, token):
        """
        Retrieve a Telegram bot record by its token.
        This method searches for a Telegram bot whose token matches the
        provided value and returns the first matching record.
        """
        return self.sudo().search([('token', '=', token)], limit=1)

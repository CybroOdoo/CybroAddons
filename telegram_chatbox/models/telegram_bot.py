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
import logging
import requests
from odoo import _, api, fields, models
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


    @api.model_create_multi
    def create(self, vals_list):
        """
        Create one or more records.
        This method extends the standard Odoo create operation and can be
        customized to perform additional processing before or after record
        creation."""

        records = super().create(vals_list)
        return records

    def write(self, vals):
        """
        Update the values of existing records.
        This method extends the standard Odoo write operation and can be
        customized to perform additional processing before or after records
        are updated."""

        res = super().write(vals)
        return res

    def action_set_webhook(self, url=None):
        """
            Configure the Telegram webhook for the selected bot(s).
            This method registers a webhook URL with the Telegram Bot API, allowing
            Telegram to send updates directly to the application. Upon successful
            registration, the bot status is updated and a success notification is
            displayed to the user.
        """
        for bot in self:
            if bot.webhook_url:
                webhook = bot.webhook_url.rstrip('/')
            else:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                if not base_url:
                    continue
                if base_url.startswith('http://'):
                    base_url = base_url.replace('http://', 'https://', 1)
                webhook = f"{base_url.rstrip('/')}/telegram/webhook/{bot.token}"
                bot.webhook_url = webhook

            api = f"https://api.telegram.org/bot{bot.token}/setWebhook"
            try:
                res = requests.post(api, json={"url": webhook}, timeout=bot.timeout)
                _logger.info("Webhook Response: %s", res.text)

                res.raise_for_status()

                info_api = f"https://api.telegram.org/bot{bot.token}/getWebhookInfo"
                info_res = requests.get(info_api, timeout=bot.timeout)
                info_res.raise_for_status()
                info_data = info_res.json()
                
                error_msg = False
                if info_data.get("ok"):
                    error_msg = info_data["result"].get("last_error_message", False)

                result = res.json()
                bot.last_sync = fields.Datetime.now()
                bot.status = 'active'
                bot.last_error_message = error_msg
                
                if result.get("ok"):
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _("Successful"),
                            'message': _(result.get("description")),
                            'type': 'success',
                            'sticky': False,
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    }

            except (ConnectionError, Timeout) as e:
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
                        'message': _(err_msg),
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
        return self.search([('token', '=', token)], limit=1)

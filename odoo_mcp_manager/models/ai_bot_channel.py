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
import secrets
import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_PLATFORM_LABELS = {
    'telegram': 'Telegram',
    'whatsapp': 'WhatsApp',
    'discord': 'Discord',
    'web': 'Web Widget',
}


class AiBotChannel(models.Model):
    """
    Configuration record for one connected chat-platform bot channel.

    Each channel stores the platform credentials and manages webhook
    registration / de-registration via its ``action_connect`` / ``action_disconnect``
    buttons.
    """
    _name = 'ai.bot.channel'
    _description = 'Bot Channel'
    _order = 'platform, name'

    name = fields.Char(required=True, default='New Bot')
    platform = fields.Selection([
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
        ('discord', 'Discord'),
        ('web', 'Web Widget'),
    ], required=True, default='telegram')
    api_token = fields.Char(
        string='Bot Token / API Key',
        groups='base.group_system',
        help='Telegram: token from @BotFather\nWhatsApp: permanent access token',
    )
    whatsapp_app_secret = fields.Char(
        string='WhatsApp App Secret',
        groups='base.group_system',
        help='Meta App Secret, used to verify the X-Hub-Signature-256 signature '
             'on incoming WhatsApp webhooks. Found in Meta App Dashboard → '
             'Settings → Basic → App Secret. Leave blank to fall back to the '
             'shared webhook secret only.',
    )
    telegram_secret_token = fields.Char(
        string='Telegram Secret Token',
        groups='base.group_system',
        readonly=True,
        help='Per-channel secret token registered with Telegram on connect and '
             'verified via the X-Telegram-Bot-Api-Secret-Token header.',
    )
    status = fields.Selection([
        ('draft', 'Not Connected'),
        ('active', 'Connected'),
        ('error', 'Error'),
    ], default='draft', readonly=True)
    bot_username = fields.Char(readonly=True)
    error_message = fields.Char(readonly=True)
    webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_urls',
        help="Register this URL on the platform's developer console.",
    )
    bot_link = fields.Char(
        string='Open Bot',
        compute='_compute_urls',
        help='Direct link to open the bot on your phone.',
    )
    whatsapp_phone_id = fields.Char(
        string='Phone Number ID',
        help='WhatsApp Cloud API → Phone Number ID (not the display number).',
    )
    custom_webhook_base = fields.Char(
        string='Public HTTPS Base URL',
        help=(
            'Override the auto-detected base URL for webhook registration.\n'
            'Required when web.base.url is localhost or HTTP.\n'
            'Example: https://abcd1234.ngrok.io\n'
            'Leave blank to use the global web.base.url setting.'
        ),
    )
    discord_public_key = fields.Char(
        string='Discord Public Key',
        help=(
            'Ed25519 public key from the Discord Developer Portal.\n'
            'Required for signature verification of incoming interactions.\n'
            'Find it at: Developer Portal → Your App → General Information → Public Key'
        ),
    )

    @api.depends('platform', 'bot_username', 'custom_webhook_base', 'status')
    def _compute_urls(self) -> None:
        """Compute the webhook registration URL and the bot's direct link."""
        params = self.env['ir.config_parameter'].sudo()
        secret = params.get_param('bot_gateway.webhook_secret', '')
        for rec in self:
            base_url = (rec.custom_webhook_base or '').rstrip('/') or \
                       params.get_param('web.base.url', '').rstrip('/')
            if rec.platform and base_url and secret:
                # For Discord, only expose the Interactions Endpoint URL after
                # the bot token has been validated (status == 'active').
                # Generating the URL before verification would let users copy
                # and register an untested endpoint in the Developer Portal.
                if rec.platform == 'discord' and rec.status != 'active':
                    rec.webhook_url = ''
                else:
                    rec.webhook_url = f'{base_url}/bot/{rec.platform}?secret={secret}'
            else:
                rec.webhook_url = ''
            if rec.platform == 'telegram' and rec.bot_username:
                rec.bot_link = f'https://t.me/{rec.bot_username}'
            elif rec.platform == 'discord' and rec.bot_username:
                rec.bot_link = f'https://discord.com/users/{rec.bot_username}'
            else:
                rec.bot_link = ''

    def _ensure_webhook_secret(self) -> str:
        """Return the global webhook secret, auto-creating it when absent."""
        params = self.env['ir.config_parameter'].sudo()
        secret = params.get_param('bot_gateway.webhook_secret', '')
        if not secret:
            secret = secrets.token_urlsafe(32)
            params.set_param('bot_gateway.webhook_secret', secret)
            _logger.info('BotChannel: auto-generated webhook secret')
        return secret

    def _base_url(self, require_https: bool = False) -> str:
        """Return the effective base URL, preferring the per-record override."""
        url = (self.custom_webhook_base or '').rstrip('/') or \
              self.env['ir.config_parameter'].sudo().get_param('web.base.url', '').rstrip('/')
        if not url:
            raise UserError(_(
                'No base URL is configured.\n\n'
                'Either:\n'
                '  • Fill in the \'Public HTTPS Base URL\' field on this channel, OR\n'
                '  • Set web.base.url in Settings → Technical → System Parameters\n\n'
                'The URL must be publicly reachable over HTTPS for webhooks.'
            ))
        if require_https and not url.startswith('https://'):
            raise UserError(_(
                'Telegram and WhatsApp require an HTTPS URL for webhooks.\n\n'
                'Current URL: %s\n\n'
                'Options:\n'
                "  1. Fill in the 'Public HTTPS Base URL' field with your HTTPS address.\n"
                '  2. Update web.base.url in Settings → Technical → System Parameters.\n\n'
                'For local testing use ngrok:\n'
                '  ngrok http 8018\n'
                "  Copy the https://...ngrok.io URL into the 'Public HTTPS Base URL' field."
            ) % url)
        return url

    def action_connect(self) -> dict:
        """Delegate to the platform-specific connect handler."""
        self.ensure_one()
        dispatcher = {
            'telegram': self._connect_telegram,
            'whatsapp': self._connect_whatsapp,
            'web': self._connect_web,
            'discord': self._connect_discord,
        }
        return dispatcher[self.platform]()

    def action_disconnect(self) -> dict:
        """Delegate to the platform-specific disconnect handler and reset status."""
        self.ensure_one()
        dispatcher = {
            'telegram': self._disconnect_telegram,
            'whatsapp': self._disconnect_whatsapp,
            'web': self._disconnect_web,
            'discord': self._disconnect_discord,
        }
        dispatcher[self.platform]()
        self.write({'status': 'draft', 'bot_username': False, 'error_message': False})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Disconnected',
                'message': f'{self.name} has been disconnected.',
                'type': 'warning',
                'sticky': False,
            },
        }


    def _connect_telegram(self) -> dict:
        """Validate the Telegram token and register the webhook."""
        token = (self.api_token or '').strip()
        if not token:
            raise UserError(_(
                'Enter your Telegram Bot Token.\n'
                'Get one from @BotFather → /newbot'
            ))
        try:
            me = requests.get(
                f'https://api.telegram.org/bot{token}/getMe', timeout=15
            ).json()
        except requests.exceptions.RequestException as exc:
            self._set_error(str(exc))
            raise UserError(_('Cannot reach Telegram API: %s') % exc) from exc

        if not me.get('ok'):
            self._set_error(me.get('description', ''))
            raise UserError(_(
                'Telegram rejected the token: %s\n\n'
                'Get a valid token from @BotFather:\n'
                '  /mybots → select your bot → API Token\n'
                '  or /newbot to create a new one'
            ) % me.get('description', 'Unknown error'))

        bot_info = me.get('result', {})
        username = bot_info.get('username', '')
        bot_name = bot_info.get('first_name', username)
        secret = self._ensure_webhook_secret()
        webhook_url = f'{self._base_url(require_https=True)}/bot/telegram?secret={secret}'

        try:
            resp = requests.post(
                f'https://api.telegram.org/bot{token}/setWebhook',
                json={'url': webhook_url, 'allowed_updates': ['message', 'callback_query']},
                timeout=15,
            ).json()
        except requests.exceptions.RequestException as exc:
            self._set_error(str(exc))
            raise UserError(f'Cannot reach Telegram API: {exc}') from exc

        if not resp.get('ok'):
            self._set_error(resp.get('description', ''))
            raise UserError(_(
                'Webhook registration failed: %(err)s\n\n'
                'Make sure your Odoo URL is reachable from the internet over HTTPS:\n'
                '%(url)s'
            ) % {'err': resp.get('description', 'Unknown error'), 'url': webhook_url})

        self.write({
            'status': 'active',
            'bot_username': username,
            'error_message': False,
            'name': self.name if self.name != 'New Bot' else f'@{username}',
        })
        _logger.info('BotChannel: Telegram @%s connected → %s', username, webhook_url)
        return self._success_notification(
            title=f'{bot_name} (@{username}) Connected',
            message=(
                f'Webhook: {webhook_url}\n'
                f'Open on your phone: https://t.me/{username}'
            ),
        )

    def _disconnect_telegram(self) -> None:
        """Remove the Telegram webhook (best-effort; local status is always reset)."""
        token = (self.api_token or '').strip()
        if token:
            try:
                requests.post(
                    f'https://api.telegram.org/bot{token}/deleteWebhook',
                    timeout=10,
                )
            except requests.exceptions.RequestException:
                pass


    def _connect_whatsapp(self) -> dict:
        """Validate WhatsApp credentials and show the webhook registration instructions."""
        if not self.api_token:
            raise UserError(_(
                'Enter your WhatsApp permanent access token.\n'
                'Meta Developer Console → WhatsApp → API Setup → Permanent Token'
            ))
        if not self.whatsapp_phone_id:
            raise UserError(_(
                'Enter the Phone Number ID.\n'
                'Meta Developer Console → WhatsApp → API Setup → Phone Number ID'
            ))
        secret = self._ensure_webhook_secret()
        webhook_url = f'{self._base_url(require_https=True)}/bot/whatsapp/verify'
        self.write({'status': 'active', 'bot_username': self.whatsapp_phone_id, 'error_message': False})
        return self._success_notification(
            title='WhatsApp Channel Ready',
            message=(
                f'Register this Verify URL in Meta Developer Console:\n{webhook_url}\n\n'
                f'Verify Token (use as hub.verify_token): {secret}\n\n'
                f'Webhook URL for messages:\n{self._base_url()}/bot/whatsapp?secret={secret}'
            ),
        )

    def _disconnect_whatsapp(self) -> None:
        """WhatsApp webhook removal is manual in Meta Console — nothing to do here."""


    def _connect_web(self) -> dict:
        """Activate the web chat widget and show the POST endpoint URL."""
        secret = self._ensure_webhook_secret()
        webhook_url = f'{self._base_url()}/bot/web?secret={secret}'
        self.write({'status': 'active', 'error_message': False})
        return self._success_notification(
            title='Web Widget Ready',
            message=f'POST messages to:\n{webhook_url}',
        )

    def _disconnect_web(self) -> None:
        """Web widget has no external webhook to remove."""


    def _connect_discord(self) -> dict:
        """
        Validate the Discord bot token and register the Interactions webhook URL.

        The Discord bot token is stored in api_token.
        The webhook URL (https://<base>/bot/discord) must be registered in the
        Discord Developer Portal → Bot → Interactions Endpoint URL.
        """
        token = (self.api_token or '').strip()
        if not token:
            raise UserError(_(
                'Enter your Discord Bot Token.\n'
                'Discord Developer Portal → Application → Bot → Reset Token'
            ))
        # Verify the token by calling the Discord /users/@me endpoint
        try:
            me = requests.get(
                'https://discord.com/api/v10/users/@me',
                headers={'Authorization': f'Bot {token}'},
                timeout=15,
            )
            if me.status_code != 200:
                err = me.json().get('message', 'Unknown error')
                self._set_error(err)
                raise UserError(_(
                    'Discord rejected the bot token: %s\n\n'
                    'Get a valid token from the Discord Developer Portal:\n'
                    '  Applications → <your app> → Bot → Reset Token'
                ) % err)
            bot_info = me.json()
        except requests.exceptions.RequestException as exc:
            self._set_error(str(exc))
            raise UserError(_('Cannot reach Discord API: %s') % exc) from exc

        secret = self._ensure_webhook_secret()
        webhook_url = f'{self._base_url(require_https=True)}/bot/discord?secret={secret}'
        bot_username = bot_info.get('username', '')
        app_id = str(bot_info.get('id', ''))

        self.write({
            'status': 'active',
            'bot_username': app_id,   # store application ID for follow-up replies
            'error_message': False,
            'name': self.name if self.name != 'New Bot' else f'Discord: {bot_username}',
        })
        _logger.info('BotChannel: Discord bot "%s" connected → %s', bot_username, webhook_url)
        return self._success_notification(
            title=f'Discord Bot "{bot_username}" Ready',
            message=(
                f'Register this Interactions Endpoint URL in the Discord Developer Portal:\n'
                f'{webhook_url}\n\n'
                f'Portal path: Applications → <your app> → General Information\n'
                f'             → Interactions Endpoint URL\n\n'
                f'Secret token (pass as ?secret= in the URL above — already included).'
            ),
        )

    def _disconnect_discord(self) -> None:
        """Discord webhooks are removed manually from the Developer Portal."""


    def _set_error(self, message: str) -> None:
        """Set status to error and record the error message."""
        self.write({'status': 'error', 'error_message': message})

    @staticmethod
    def _success_notification(title: str, message: str) -> dict:
        """Build a display_notification client action dict."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': 'success',
                'sticky': True,
            },
        }

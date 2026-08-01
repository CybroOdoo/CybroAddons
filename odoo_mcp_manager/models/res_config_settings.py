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
import secrets
from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    """Adds Bot Gateway configuration fields to the standard Settings form."""

    _inherit = 'res.config.settings'

    bot_webhook_secret = fields.Char(
        string='Webhook Secret',
        config_parameter='bot_gateway.webhook_secret',
        groups='base.group_system',
        help=(
            'Shared secret appended to all bot webhook URLs as ?secret=. '
            'Auto-generated on first bot connect.'
        ),
    )
    bot_mcp_api_key = fields.Char(
        string='Bot MCP API Key',
        config_parameter='bot_gateway.mcp_api_key',
        groups='base.group_system',
        help='API key used by the bot gateway to call internal MCP tools.',
    )
    mcp_enforce_tool_allowlist = fields.Boolean(
        string='Enforce Tool Access Allow-list',
        config_parameter='mcp_gateway.enforce_allowlist',
        default=True,
        help='When enabled, the generic built-in AI tools may only read or '
             'modify models listed under Configuration → Tool Access Rules. '
             'Disabling lets tools touch any model (not recommended).',
    )

    def action_generate_webhook_secret(self) -> dict:
        """Generate a new cryptographically random webhook secret and save it."""
        new_secret = secrets.token_urlsafe(32)
        self.env['ir.config_parameter'].sudo().set_param(
            'bot_gateway.webhook_secret', new_secret
        )
        self.bot_webhook_secret = new_secret
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Webhook Secret Generated'),
                'message': _('A new secret has been saved. '
                             'Re-connect any active bot channels.'),
                'type': 'warning',
                'sticky': False,
            },
        }

    def action_generate_mcp_api_key(self) -> dict:
        """Generate a new MCP API key for the bot gateway and save it."""
        new_key = self.env['res.users.apikeys']._generate('rpc', 'Bot Gateway MCP Key', None)
        self.env['ir.config_parameter'].sudo().set_param('bot_gateway.mcp_api_key', new_key)
        self.bot_mcp_api_key = new_key
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('MCP API Key Generated'),
                'message': _('Key created and saved. '
                             'The bot can now call internal MCP tools.'),
                'type': 'success',
                'sticky': False,
            },
        }

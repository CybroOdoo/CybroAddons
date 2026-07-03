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
import uuid
from odoo import api, fields, models


class AiSession(models.Model):
    """
    Tracks an active MCP protocol session.

    One record is created per (user, mcp_source) pair so that different clients
    — Claude Desktop, Telegram bot, Discord bot, etc. — each appear as their own
    session rather than all collapsing into a single row.
    """

    _name = 'ai.session'
    _description = 'AI Session'

    session_id = fields.Char(
        required=True,
        index=True,
        default=lambda self: str(uuid.uuid4()),
    )
    user_id = fields.Many2one(
        'res.users',
        string='Odoo User',
        required=True,
        default=lambda self: self.env.user,
    )
    mcp_source = fields.Char(
        string='Client Source',
        index=True,
        default='mcp',
        help=(
            'Identifies which client owns this session.\n'
            'Values set by X-Odoo-MCP-Source header:\n'
            '  • mcp   — Claude Desktop / direct MCP clients\n'
            '  • bot   — Telegram / WhatsApp / Web bot gateway\n'
            '  • discord — Discord bot gateway\n'
            'One active session is kept per (user, mcp_source) pair.'
        ),
    )
    state = fields.Selection([
        ('not_initialized', 'Not Initialized'),
        ('initializing', 'Initializing'),
        ('initialized', 'Initialized'),
        ('terminated', 'Terminated'),
    ], default='not_initialized', required=True)
    protocol_version = fields.Char(string='MCP Version')
    client_name = fields.Char(string='Client Name')
    client_version = fields.Char(string='Client Version')
    user_agent = fields.Char(string='User Agent')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('session_id_unique', 'unique(session_id)', 'Session ID must be unique!'),
    ]

    _VALID_TRANSITIONS = {
        'not_initialized': ['initializing'],
        'initializing': ['initialized'],
        'initialized': ['terminated'],
    }

    def transition_to(self, state: str) -> None:
        """Move the session to *state* if the transition is allowed; silently ignore invalid ones."""
        self.ensure_one()
        if state in self._VALID_TRANSITIONS.get(self.state, []):
            self.state = state

    def terminate(self) -> None:
        """Mark the session inactive and set its state to terminated."""
        self.write({'active': False, 'state': 'terminated'})

    @api.model
    def create_new_session(self, user_id: int) -> 'AiSession':
        """Create and return a new session record for the given Odoo user ID."""
        return self.create({
            'user_id': user_id,
            'state': 'not_initialized',
        })

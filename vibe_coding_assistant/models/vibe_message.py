# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
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
################################################################################

from odoo import models, fields


class VibeMessage(models.Model):
    """Model for managing Vibe messages."""
    _name = "vibe.message"
    _description = "Vibe Message"
    _rec_name = "content"
    _order = "create_date asc, id asc"

    conversation_id = fields.Many2one(
        "vibe.conversation",
        string="Conversation",
        required=True,
        ondelete="cascade",
        index=True,
        help="Conversation ID",
    )
    role = fields.Selection(
        [("user", "User"), ("assistant", "Assistant"), ("system", "System")],
        string="Role",
        required=True,
        help="Role of the conversation.",
    )
    content = fields.Text(string="Content", required=True,help="Content of the message")
    sequence = fields.Integer(string="Sequence", default=10,help="Sequence of the conversation")
    generated_module_id = fields.Many2one(
        "vibe.generated.module",
        string="Generated Module",
        ondelete="set null",
        help="Set on assistant messages that produced a generated module.",
    )

    # ── Token usage ─────────────────────────────────────────────────────
    # Populated on assistant messages from the provider's response metadata.
    tokens_input = fields.Integer(
        string="Input Tokens",
        help="Tokens in the prompt sent to the provider (input cost).",
    )
    tokens_output = fields.Integer(
        string="Output Tokens",
        help="Tokens in the model's response (output cost).",
    )
    tokens_used = fields.Integer(
        string="Total Tokens",
        help="input + output. Total tokens charged by the provider.",
    )

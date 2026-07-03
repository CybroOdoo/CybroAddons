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
from odoo import fields, models


class AiBotMessage(models.Model):
    """A single user or assistant message stored inside a bot conversation."""

    _name = 'ai.bot.message'
    _description = 'Bot Conversation Message'
    _order = 'create_date desc, id desc'
    _rec_name = 'content'

    conversation_id = fields.Many2one(
        'ai.bot.conversation', required=True, ondelete='cascade', index=True,
    )
    role = fields.Selection([
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ], required=True, default='user')
    content = fields.Text(required=True, string='Content')
    tool_used = fields.Char(
        string='Tool Used',
        help='Name of the MCP tool invoked to generate this reply (e.g. ask_ai)',
    )

# -*- coding: utf-8 -*-
from odoo import models, fields


class AiBotMessage(models.Model):
    """A single user or assistant message stored inside a bot conversation."""

    _name = 'ai.bot.message'
    _description = 'Bot Conversation Message'
    _order = 'create_date desc'
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

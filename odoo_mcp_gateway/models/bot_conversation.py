# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AiBotConversation(models.Model):
    """
    Persistent conversation record that tracks the chat history for one
    platform user, keyed by ``platform:platform_user_id``.
    """

    _name = 'ai.bot.conversation'
    _description = 'Bot Conversation (Chat Memory)'
    _order = 'last_message_date desc, id desc'
    _rec_name = 'session_key'

    session_key = fields.Char(
        required=True, index=True, copy=False,
        help='Composite key: platform:platform_user_id  e.g. telegram:123456789',
    )
    platform = fields.Selection([
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
        ('web', 'Web Chat'),
    ], required=True, string='Platform')
    platform_user_id = fields.Char(
        required=True, index=True, string='Platform User ID'
    )
    platform_user_name = fields.Char(
        string='User Name',
        help='Display name or @username of the platform user (e.g. Telegram @username).',
    )
    bot_channel_id = fields.Many2one(
        'ai.bot.channel', string='Bot Channel', ondelete='set null',
        help='The bot channel that received this conversation.',
    )
    odoo_user_id = fields.Many2one(
        'res.users', string='Linked Odoo User', ondelete='set null'
    )
    message_ids = fields.One2many(
        'ai.bot.message', 'conversation_id', string='Messages'
    )
    message_count = fields.Integer(
        string='Messages', compute='_compute_message_count'
    )
    last_message_date = fields.Datetime(
        string='Last Message', readonly=True, index=True,
        help='Updated automatically each time a message is added.',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('session_key_unique', 'unique(session_key)',
         'A conversation for this platform user already exists!'),
    ]

    @api.depends('message_ids')
    def _compute_message_count(self) -> None:
        for rec in self:
            rec.message_count = len(rec.message_ids)

    @api.model
    def get_or_create(
        self,
        platform: str,
        platform_user_id: str,
        platform_user_name: str = '',
        bot_channel_id: int = False,
    ) -> 'AiBotConversation':
        """Return the existing conversation for this user, creating one if absent."""
        key = f'{platform}:{platform_user_id}'
        conv = self.search([('session_key', '=', key)], limit=1)
        if not conv:
            conv = self.create({
                'session_key':        key,
                'platform':           platform,
                'platform_user_id':   platform_user_id,
                'platform_user_name': platform_user_name or False,
                'bot_channel_id':     bot_channel_id or False,
            })
            _logger.info('BotGateway: new conversation created — %s (bot_channel=%s)', key, bot_channel_id)
        else:
            updates = {}
            if platform_user_name and conv.platform_user_name != platform_user_name:
                updates['platform_user_name'] = platform_user_name
            if bot_channel_id and conv.bot_channel_id.id != bot_channel_id:
                updates['bot_channel_id'] = bot_channel_id
            if updates:
                conv.write(updates)
        return conv

    def get_recent_messages(self, limit: int = 10) -> list:
        """Return the last *limit* messages in chronological order for LLM context."""
        self.ensure_one()
        msgs = self.message_ids.sorted('create_date', reverse=True)[:limit]
        return [{'role': m.role, 'content': m.content} for m in reversed(msgs)]

    def add_message(
        self, role: str, content: str, tool_used: str = None
    ) -> None:
        """Append one message to this conversation and refresh last_message_date."""
        self.ensure_one()
        now = fields.Datetime.now()
        self.env['ai.bot.message'].create({
            'conversation_id': self.id,
            'role': role,
            'content': content,
            'tool_used': tool_used or False,
        })
        self.write({'last_message_date': now})

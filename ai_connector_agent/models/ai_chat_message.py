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
from odoo import models, fields, api


class AiChatMessage(models.Model):
    """Store individual user and AI messages within a chat session."""

    _name = 'ai.chat.message'
    _description = 'AI Chat Message'
    _order = 'create_date asc'

    session_id = fields.Many2one(comodel_name='ai.chat.session', string='Session', required=True, ondelete='cascade', help="The specific chat session this message belongs to.")
    message_type = fields.Selection(selection=[
        ('user', 'User'),
        ('ai', 'AI')
    ], string='Type', required=True, help="Specifies if the message was sent by the human user or the AI Assistant.")
    content = fields.Text(string='Content', required=True, help="The plain text content of the message.")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', help="Images or documents attached to this message.")
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, help="The exact date and time the message was recorded.")

    user_id = fields.Many2one(comodel_name='res.users', string='User', default=lambda self: self.env.user, help="The user account linked to this message.")

    @api.model_create_multi
    def create(self, vals):
        """Update session's last message date when creating message"""
        message = super().create(vals)
        message.session_id.last_message_date = message.timestamp
        return message

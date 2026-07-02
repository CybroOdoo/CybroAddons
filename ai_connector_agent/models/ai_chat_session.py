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
from odoo import models, fields


class AiChatSession(models.Model):
    """Manage AI chat sessions and their related conversation messages."""

    _name = 'ai.chat.session'
    _description = 'AI Chat Session'
    _order = 'create_date desc'

    name = fields.Char(string='Session Name', required=True, help="A descriptive name for the chat session (e.g. AI Agent Name - Model ID - Date).")
    ai_agent_id = fields.Many2one(comodel_name='ai.providers', string='AI Agent', required=True, help="The AI Provider or Agent used for this chat session.")
    ai_model_id = fields.Many2one(comodel_name='ai.model', string='AI Model', required=True, help="The specific AI Model (e.g. GPT-4, Gemini Pro) used for this chat session.")
    user_id = fields.Many2one(comodel_name='res.users', string='User', default=lambda self: self.env.user, required=True, help="The owner of this chat session.")
    message_ids = fields.One2many(comodel_name='ai.chat.message', inverse_name='session_id', string='Messages', help="The collection of messages exchanged during this session.")
    is_active = fields.Boolean(string='Active', default=True, help="Indicates if the session is currently active or has been cleared/archived.")
    last_message_date = fields.Datetime(string='Last Message Date', help="The timestamp of the most recent interaction in this session.")

    def get_or_create_session(self, ai_agent_id, ai_model_id, user_id=None):
        """Get existing active session or create new one"""
        if not user_id:
            user_id = self.env.user.id

        # Try to find existing active session
        existing_session = self.search([
            ('ai_agent_id', '=', ai_agent_id),
            ('ai_model_id', '=', ai_model_id),
            ('user_id', '=', user_id),
            ('is_active', '=', True)
        ], limit=1)

        if existing_session:
            return existing_session

        # Create new session
        agent = self.env['ai.providers'].browse(ai_agent_id)
        model = self.env['ai.model'].browse(ai_model_id)

        session_name = f"{agent.name} - {model.modelId} - {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')}"

        return self.create({
            'name': session_name,
            'ai_agent_id': ai_agent_id,
            'ai_model_id': ai_model_id,
            'user_id': user_id,
        })

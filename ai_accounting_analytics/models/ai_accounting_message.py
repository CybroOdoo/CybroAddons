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
from odoo import fields, models


class AiAccountingMessage(models.Model):
    """One message of a conversation.

    ``parts`` is what the user sees (text, tables, charts, KPI cards in
    arrival order); ``history_digest`` is what the AI sees in later turns.
    """
    _name = 'ai.accounting.message'
    _description = 'AI Analytics Message'
    _order = 'id'

    chat_id = fields.Many2one('ai.accounting.chat', string='Conversation', required=True,
                              ondelete='cascade', index=True)
    user_id = fields.Many2one(related='chat_id.user_id', store=True, index=True)
    company_id = fields.Many2one(related='chat_id.company_id', store=True)
    role = fields.Selection([('user', 'User'), ('assistant', 'Assistant')], required=True)
    content = fields.Text()
    parts = fields.Json()
    steps = fields.Json()
    history_digest = fields.Text()
    error = fields.Boolean()
    model_id = fields.Many2one('ai.accounting.model', string='Model', ondelete='set null')
    input_tokens = fields.Integer()
    cached_tokens = fields.Integer()
    output_tokens = fields.Integer()
    cost = fields.Float(string='Cost (USD)', digits=(16, 6))
    duration_ms = fields.Integer(string='Duration (ms)')

    def _ai_to_client(self):
        self.ensure_one()
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content or '',
            'parts': self.parts or ([{'type': 'text', 'text': self.content}]
                                    if self.content else []),
            'steps': self.steps or [],
            'error': self.error,
            'model': self.model_id.name or '',
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'cost': self.cost,
            'duration_ms': self.duration_ms,
        }

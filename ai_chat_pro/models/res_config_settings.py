# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError

from .ai_chat_assistant import DEFAULT_AI_MODEL, DEFAULT_MAX_ROWS
from .ai_chat_reasoning import get_reasoning_models
from .ai_chat_voice import DEFAULT_VOICE_MODEL, get_voice_model, get_voice_models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_chat_pro_openrouter_key = fields.Char(
        string="OpenRouter API Key", config_parameter='ai_chat_pro.openrouter_api_key', groups='base.group_system',
    )
    ai_chat_pro_model = fields.Char(
        string="AI Model", config_parameter='ai_chat_pro.model', default=DEFAULT_AI_MODEL,
        help="Decision model of OpenRouter's Decisions API, e.g. ~typesafe/jev-latest or typesafe/jev-1.13.",
    )
    ai_chat_pro_use_olg = fields.Boolean(
        string="Reasoning with Odoo AI", config_parameter='ai_chat_pro.use_olg',
        help="Questions that need an analysis are answered by Odoo's AI service (OLG), from the data found.",
    )
    ai_chat_pro_reasoning_openrouter = fields.Boolean(
        string="OpenRouter Model instead of Odoo AI", config_parameter='ai_chat_pro.reasoning_openrouter',
        help="The analyses, the values of records to create, the charts and the report summaries are written by a "
             "model of OpenRouter, with the key above, instead of Odoo's AI service. Without a model chosen, "
             "Odoo's AI service writes them.",
    )
    ai_chat_pro_reasoning_model = fields.Selection(
        selection='_get_reasoning_model_selection',
        string="Reasoning Model", config_parameter='ai_chat_pro.reasoning_model',
        help="Model of OpenRouter replacing Odoo's AI service, among those reading and writing text, cheapest first.",
    )
    ai_chat_pro_deep_analysis = fields.Boolean(
        string="Deep Analysis", config_parameter='ai_chat_pro.deep_analysis',
        help="Questions asking for a decision (\"how can I increase the sales of this product\") are answered "
             "from several sets of data the user can access, with findings, recommendations, risks and next "
             "steps, written by Odoo AI or the OpenRouter model above. The agent switches to it on its own when "
             "the decision model is confident enough that a question needs it; users can also turn it on in the "
             "chat.",
    )
    # on by default: kept as 'True' or 'False', as an unticked setting would remove its parameter
    ai_chat_pro_agent_thinking = fields.Boolean(
        string="Agent Thinking", compute='_compute_ai_chat_pro_agent_thinking',
        inverse='_inverse_ai_chat_pro_agent_thinking', readonly=False,
        help="The agent thinks with Odoo AI (or the OpenRouter model above) when a request needs it: requests "
             "needing several steps are answered one data question after the other, and an answer that found "
             "nothing is reflected on and asked again once in a better way. Simple questions cost nothing more.",
    )
    ai_chat_pro_deep_confidence = fields.Float(
        string="Deep Analysis Confidence", config_parameter='ai_chat_pro.deep_confidence', default=0.6,
        help="Confidence of the decision model, from 0 to 1, above which the agent answers a question with a deep "
             "analysis on its own. Higher: fewer, cheaper analyses. Below it, the data is shown with a short "
             "explanation.",
    )
    ai_chat_pro_chart_olg = fields.Boolean(
        string="Charts with Odoo AI", config_parameter='ai_chat_pro.chart_olg',
        help="When a question asks for a given chart, or several values could be drawn, Odoo's AI service (OLG) "
             "chooses the chart from the names of the columns. Otherwise charts are chosen without AI.",
    )
    ai_chat_pro_allow_create = fields.Boolean(
        string="Create Records", config_parameter='ai_chat_pro.allow_create',
        help="Users can ask the assistant to create records, e.g. \"create a sales order for Azure Interior with "
             "3 chairs\". Odoo's AI service reads the values of the request. Users confirm each record before it "
             "is created, with their own access rights.",
    )
    ai_chat_pro_voice = fields.Boolean(
        string="Voice Questions", config_parameter='ai_chat_pro.voice',
        help="Users can ask their questions out loud: the recording is turned into text by a model of OpenRouter, "
             "with the key above.",
    )
    ai_chat_pro_voice_model = fields.Selection(
        selection='_get_voice_model_selection',
        string="Speech to Text Model", config_parameter='ai_chat_pro.voice_model', default=DEFAULT_VOICE_MODEL,
        help="Model of OpenRouter turning voice questions into text, among those reading audio, cheapest first.",
    )
    ai_chat_pro_max_rows = fields.Integer(
        string="Maximum Rows", config_parameter='ai_chat_pro.max_rows', default=DEFAULT_MAX_ROWS,
        help="Maximum number of records or groups shown in an answer.",
    )

    @api.model
    def _get_voice_model_selection(self):
        """ The models of OpenRouter reading audio, with the one chosen, even when they
        can not be listed (OpenRouter unreachable). """
        selection = get_voice_models()
        chosen = get_voice_model(self.env)
        listed = dict(selection)
        missing = [model_id for model_id in dict.fromkeys([chosen, DEFAULT_VOICE_MODEL]) if model_id not in listed]
        return [(model_id, model_id) for model_id in missing] + selection

    @api.model
    def _get_reasoning_model_selection(self):
        """ The models of OpenRouter writing text, with the one chosen, even when they
        can not be listed (OpenRouter unreachable). """
        selection = get_reasoning_models()
        chosen = self.env['ir.config_parameter'].sudo().get_param('ai_chat_pro.reasoning_model')
        if chosen and chosen not in dict(selection):
            selection = [(chosen, chosen)] + selection
        return selection

    def _compute_ai_chat_pro_agent_thinking(self):
        enabled = self.env['ai.chat.assistant']._is_thinking_enabled()
        for settings in self:
            settings.ai_chat_pro_agent_thinking = enabled

    def _inverse_ai_chat_pro_agent_thinking(self):
        for settings in self:
            self.env['ir.config_parameter'].sudo().set_param(
                'ai_chat_pro.agent_thinking', 'True' if settings.ai_chat_pro_agent_thinking else 'False')

    def action_ai_chat_pro_test_connection(self):
        self.ensure_one()
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False}
        if not self.ai_chat_pro_openrouter_key:
            raise UserError(self.env._("Please set the OpenRouter API key first."))
        answers = self.env['ai.chat.assistant']._decide(
            "List me the top 10 sales orders", {
                'kind': {
                    'type': 'choice',
                    'instructions': "What kind of answer does the question ask for?",
                    'criteria': {'list': "A list of records", 'count': "A number of records"},
                },
            }, usage, api_key=self.ai_chat_pro_openrouter_key, ai_model=self.ai_chat_pro_model or DEFAULT_AI_MODEL,
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': self.env._("Connection successful"),
                'message': self.env._(
                    "The model answered \"%(answer)s\" (%(tokens)s tokens, $%(cost)s).",
                    answer=(answers.get('kind') or {}).get('choice') or '?',
                    tokens=usage['prompt_tokens'] + usage['completion_tokens'], cost=f"{usage['cost']:.6f}",
                ),
                'sticky': False,
            },
        }

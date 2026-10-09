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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_accounting_default_model_id = fields.Many2one(
        'ai.accounting.model', string='Default AI Model',
        config_parameter='ai_accounting_analytics.default_model_id')
    ai_accounting_max_steps = fields.Integer(
        string='Max AI Steps', default=5,
        config_parameter='ai_accounting_analytics.max_steps',
        help="Maximum AI calls per answer (each tool round is one call).")
    ai_accounting_history_turns = fields.Integer(
        string='History Turns', default=4,
        config_parameter='ai_accounting_analytics.history_turns',
        help="Previous question/answer pairs sent with a new question (as short digests).")
    ai_accounting_max_output_tokens = fields.Integer(
        string='Max Answer Tokens', default=1024,
        config_parameter='ai_accounting_analytics.max_output_tokens')
    ai_accounting_model_rows = fields.Integer(
        string='Rows Sent to the AI', default=15,
        config_parameter='ai_accounting_analytics.model_rows',
        help="Table rows sent back to the AI; users always see the full table.")

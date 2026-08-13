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
import requests
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    """Expose Pivot AI Summary provider and model settings in Odoo."""

    _inherit = 'res.config.settings'

    enable_pivot_ai_summary = fields.Boolean(
        string="Enable Pivot AI Summary",
        config_parameter="pivot_ai_summary.enable"
    )

    generative_ai_systems = fields.Selection([
        ('odoo', 'Odoo AI (Internal / IAP)'),
        ('openai', 'Open AI'),
        ('openrouter', 'OpenRouter'),
        ('gemini', 'Google Gemini')
    ], string='Generative AI Systems', config_parameter='pivot_ai_summary.system')

    api_key = fields.Char('API Key', config_parameter='pivot_ai_summary.api_key')

    gemini_model_id = fields.Selection(
        selection=[
            ('gemini-2.0-flash', 'Gemini 2.0 Flash (Free, Recommended)'),
            ('gemini-2.0-flash-lite', 'Gemini 2.0 Flash Lite (Fastest, Free)'),
            ('gemini-2.5-pro-exp-03-25', 'Gemini 2.5 Pro Experimental (Most Powerful, Free)'),
        ],
        string="Gemini Model",
        config_parameter='pivot_ai_summary.gemini_model',
    )

    model_id = fields.Selection(selection=[
        ('gpt-4o', 'gpt-4o'),
        ('gpt-4o-mini', 'gpt-4o-mini'),
        ('gpt-4-turbo', 'gpt-4-turbo'),
    ], string="OpenAI Model", config_parameter='pivot_ai_summary.openai_model')

    openrouter_model_id = fields.Selection(
        selection='_get_openrouter_models',
        string="OpenRouter Model",
        config_parameter='pivot_ai_summary.openrouter_model'
    )

    def _get_openrouter_models(self):
        """Return OpenRouter models using the configured API key.

        A descriptive fallback choice is returned when credentials are missing
        or the OpenRouter service cannot be reached.
        """
        icp = self.env['ir.config_parameter'].sudo()
        api_key = self.api_key or icp.get_param('pivot_ai_summary.api_key')
        if not api_key:
            return [('none', 'Please enter API Key and click Save')]
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'HTTP-Referer': icp.get_param('web.base.url', 'http://localhost:8069'),
                'X-Title': 'Odoo Pivot AI',
            }
            response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json().get('data', [])
                model_list = [(m.get('id'), m.get('name', m.get('id'))) for m in data]
                return sorted(model_list, key=lambda x: 'free' not in x[1].lower())
            return [('none', f'API Error {response.status_code}')]
        except Exception:
            return [('none', 'Connection Error')]

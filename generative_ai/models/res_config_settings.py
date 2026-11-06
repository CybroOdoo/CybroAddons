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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    generative_ai_systems = fields.Selection([
        ('openai', 'OpenAI'),
        ('openrouter', 'OpenRouter')
    ], string='Generative AI Systems')
    api_key = fields.Char('API Key', copy=False)
    max_token = fields.Char(string='Maximum tokens',
                            default='4096', config_parameter='generative_ai.max_token')
    model_id = fields.Selection(selection=[
        ('gpt-3.5-turbo', 'gpt-3.5-turbo'),
        ('gpt-4-turbo', 'gpt-4-turbo'),
        ('gpt-4o', 'gpt-4o'),
        ('gpt-4o-mini', 'gpt-4o-mini'),
        ('gpt-4-0613', 'gpt-4-0613'),
    ])
    openrouter_model_id = fields.Selection(selection='_get_model_selection',
                                           string="AI Model")

    @api.model
    def default_get(self, fields):
        """Override default_get to set a default value for 'max_token' field
        when it is included in the fields to fetch."""
        res = super().default_get(fields)
        if 'max_token' in fields:
            res['max_token'] = "4096"
        return res

    @api.model
    def get_values(self):
        """Override get_values to load saved configuration parameters from the system settings.
        These values are shown on the settings UI."""
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res['generative_ai_systems'] = ICP.get_str('generative_ai_systems') or False
        res['api_key'] = ICP.get_str('api_key') or False
        res['model_id'] = ICP.get_str('model_id') or False
        res['openrouter_model_id'] = ICP.get_str('openrouter_model_id') or False
        res['max_token'] = ICP.get_str('max_token') or '4096'
        return res

    @api.onchange('generative_ai_systems')
    def _onchange_generative_ai_systems(self):
        """Clear model selection when system or API key changes"""
        if not self.generative_ai_systems or not self.api_key:
            self.model_id = False
            self.openrouter_model_id = False

    def _get_model_selection(self):
        """Return list of tuples for model selection"""
        try:
            ICP = self.env['ir.config_parameter'].sudo()
            config_system = ICP.get_str('generative_ai_systems')
            config_key = ICP.get_str('api_key')
            ai_system = self.generative_ai_systems or config_system
            api_key = self.api_key or config_key
            if ai_system and api_key:
                if ai_system == 'openrouter':
                    url = "https://openrouter.ai/api/v1/models"
                    # Required headers for OpenRouter API
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'HTTP-Referer': ICP.get_str('web.base.url', ''),
                        'X-Title': 'Odoo Integration'
                    }
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        models = response.json().get('data',
                                                     [])  # OpenRouter returns models in 'data' field
                        if models:
                            model_list = [(str(model['id']), str(model['name'])) for model
                                          in models]
                            return model_list
                        else:
                            return [('none', 'No Models Available')]
                    else:
                        return [('none', f'API Error: {response.status_code}')]
        except requests.exceptions.RequestException:
            return [('none', 'Connection Error')]
        except Exception:
            return [('none', 'Error Loading Models')]
        return [('none', 'No Models Available')]

    def set_values(self):
        """Save settings and fetch models"""
        res = super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_str('generative_ai_systems', self.generative_ai_systems or False)
        ICP.set_str('api_key', self.api_key or False)
        ICP.set_str('max_token', self.max_token or '4096')
        if self.generative_ai_systems == 'openrouter':
            ICP.set_str('openrouter_model_id', self.openrouter_model_id or False)
            ICP.set_str('model_id', False)
        else:
            ICP.set_str('model_id', self.model_id or False)
            ICP.set_str('openrouter_model_id', False)
        if self.generative_ai_systems and self.api_key:
            models = self._get_model_selection()
            if models and models != [('none', 'No Models Available')]:
                # Only save model_id if it's in the list of available models
                if self.openrouter_model_id and any(
                        self.openrouter_model_id == model[0] for model in models):
                    ICP.set_str('openrouter_model_id', self.openrouter_model_id)
                else:
                    # If current model_id is not in available models, set to first available model
                    ICP.set_str('openrouter_model_id', models[0][0])
                    self.openrouter_model_id = models[0][0]
            else:
                ICP.set_str('openrouter_model_id', False)
                self.openrouter_model_id = False
        return res

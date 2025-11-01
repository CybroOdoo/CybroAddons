# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import requests
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    generative_ai_systems = fields.Selection([
        ('openai', 'Open AI'),
        ('openrouter', 'OpenRouter')
    ], string='Generative AI Systems')
    api_key = fields.Char('API Key', copy=False)
    max_token = fields.Char(string='Maximum tokens',
                            default=4096, config_parameter='generative_ai.max_token')
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
        res = super(ResConfigSettings, self).default_get(fields)
        if 'max_token' in fields:
            res['max_token'] = "4096"
        return res

    @api.model
    def get_values(self):
        """Override get_values to load saved configuration parameters from the system settings.
        These values are shown on the settings UI."""
        res = super(ResConfigSettings, self).get_values()
        res['generative_ai_systems'] = self.env['ir.config_parameter'].sudo().get_param(
            'generative_ai_systems')
        res['api_key'] = self.env['ir.config_parameter'].sudo().get_param('api_key')
        res['model_id'] = self.env['ir.config_parameter'].sudo().get_param('model_id')
        res['openrouter_model_id'] = self.env['ir.config_parameter'].sudo().get_param(
            'openrouter_model_id')
        res['max_token'] = self.env['ir.config_parameter'].sudo().get_param('max_token')
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
            config_system = self.env['ir.config_parameter'].sudo().get_param(
                'generative_ai_systems')
            config_key = self.env['ir.config_parameter'].sudo().get_param('api_key')
            ai_system = self.generative_ai_systems or config_system
            api_key = self.api_key or config_key
            if ai_system and api_key:
                if ai_system == 'openrouter':
                    url = "https://openrouter.ai/api/v1/models"
                    # Required headers for OpenRouter API
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'HTTP-Referer': self.env['ir.config_parameter'].sudo().get_param(
                            'web.base.url', ''),
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
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('generative_ai_systems',
                                                         self.generative_ai_systems)
        self.env['ir.config_parameter'].sudo().set_param('api_key', self.api_key)
        self.env['ir.config_parameter'].sudo().set_param('max_token', self.max_token)
        if self.generative_ai_systems == 'openrouter':
            self.env['ir.config_parameter'].sudo().set_param('openrouter_model_id',
                                                             self.openrouter_model_id)
            self.env['ir.config_parameter'].sudo().set_param('model_id',
                                                             '')
        else:
            self.env['ir.config_parameter'].sudo().set_param('model_id', self.model_id)
        if self.generative_ai_systems and self.api_key:
            models = self._get_model_selection()
            if models and models != [('none', 'No Models Available')]:
                # Only save model_id if it's in the list of available models
                if self.openrouter_model_id and any(
                        self.openrouter_model_id == model[0] for model in models):
                    self.env['ir.config_parameter'].sudo().set_param(
                        'openrouter_model_id', self.openrouter_model_id)
                else:
                    # If current model_id is not in available models, set to first available model
                    self.env['ir.config_parameter'].sudo().set_param(
                        'openrouter_model_id', models[0][0])
                    self.openrouter_model_id = models[0][0]
            else:
                self.env['ir.config_parameter'].sudo().set_param('openrouter_model_id', '')
                self.openrouter_model_id = False

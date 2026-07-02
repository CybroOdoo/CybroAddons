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
from odoo import models, fields, _
from odoo.exceptions import UserError


class AIProviders(models.Model):
    """Configure AI providers and retrieve their available models."""

    _name = "ai.providers"
    _description = "AI Provider"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", required=True, help="Name of the AI provider (e.g. OpenAI, Anthropic, Google Gemini).")
    api_key = fields.Char(string="Api Key", required=True, help="The individual API key used for authentication with this provider.")
    api_base_url = fields.Char(string="Api Base Url", required=True, help="The root URL for the provider's API endpoints.")
    fetch_model_endpoint = fields.Char(string="Fetch model endpoint", help="The specific endpoint path used to retrieve available AI models (defaults to /v1/models).")
    ai_model_ids = fields.Many2many(string="Ai Model", comodel_name='ai.model', readonly=True, ondelete='cascade', help="The collection of AI models currently supported by and fetched from this provider.")
    provider_image = fields.Image(
        string='Image',
        max_width=1920,
        max_height=1920,
        help="Provider image."
    )

    def action_fetch_models(self):
        """Fetch available AI models from the provider and link them."""
        self.ensure_one()
        base_url = self.api_base_url
        api_key = self.api_key
        fetch_model_endpoint = self.fetch_model_endpoint or "/v1/models"
        endpoint = base_url.rstrip("/") + "/" + fetch_model_endpoint.lstrip("/")

        try:
            headers = {}
            params = {}
            provider_name = (self.name or "").lower()
            base_url_lower = (self.api_base_url or "").lower()
            
            if "openai" in provider_name or "chatgpt" in provider_name or "openai" in base_url_lower:
                headers['Authorization'] = f"Bearer {api_key}"
            elif "anthropic" in provider_name or "anthropic" in base_url_lower:
                headers['x-api-key'] = api_key
                headers['anthropic-version'] = '2023-06-01'
            else:
                # Default to Gemini style
                params = {"key": api_key}

            response = requests.get(endpoint, params=params, headers=headers)

            if response.status_code != 200:
                raise UserError(f"Error {response.status_code}: {response.text}")
            try:
                data = response.json()
            except ValueError:
                raise UserError("Invalid JSON response from the AI provider.")
            if not isinstance(data, dict):
                raise UserError("Unexpected API response structure (not a dict).")
                
            models_list = []
            if 'models' in data:
                models_list = data['models']
            elif 'data' in data and isinstance(data['data'], list):
                models_list = data['data']
            else:
                raise UserError("Unexpected API response structure. Could not find models list.")

            if not models_list:
                raise UserError(_("There is no models"))

            model_ids = []
            seen_model_ids = set()
            for record in models_list:
                # OpenAI uses 'id', Gemini uses 'name'
                m_id = record.get('id') or record.get('name')
                if not m_id:
                    continue
                clean_id = m_id.replace("models/", "").strip()

                if clean_id in seen_model_ids:
                    continue
                seen_model_ids.add(clean_id)

                existing_model = self.env['ai.model'].search([('modelId', '=', clean_id)], limit=1)
                if existing_model:
                    model_ids.append(existing_model.id)
                else:
                    new_model = self.env['ai.model'].create({
                        'modelId': clean_id,
                        'version': record.get('version', ''),
                        'object': record.get('displayName') or record.get('object', ''),
                    })

                    model_ids.append(new_model.id)
            self.write({
                'ai_model_ids': [fields.Command.link(model_id) for model_id in model_ids]
            })

        except requests.exceptions.RequestException as e:
            raise UserError(f"Request failed: {e}")

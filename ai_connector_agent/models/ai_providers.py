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
#############################################################################
import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AIProvider(models.Model):
    """Configure AI providers and retrieve their available models."""

    _name = 'ai.provider'
    _description = 'AI Provider'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Name",
        required=True,
        help="Name of the AI provider (e.g. OpenAI, Anthropic, Google Gemini)."
    )
    api_key = fields.Char(
        string="API Key",
        required=True,
        groups='base.group_system',
        help="The individual API key used for authentication with this provider."
    )
    api_base_url = fields.Char(
        string="API Base URL",
        required=True,
        help="The root URL for the provider's API endpoints."
    )
    fetch_model_endpoint = fields.Char(
        string="Fetch Model Endpoint",
        help="The specific endpoint path used to retrieve available AI models "
             "(defaults to /v1/models)."
    )
    ai_model_ids = fields.Many2many(
        string="AI Models",
        comodel_name='ai.model',
        readonly=True,
        ondelete='cascade',
        help="The collection of AI models currently supported by and fetched from this provider."
    )
    provider_image = fields.Image(
        string='Image',
        max_width=1920,
        max_height=1920,
        help="Provider logo or image."
    )

    def action_fetch_models(self):
        """Fetch available AI models from the provider and link them."""
        self.ensure_one()
        # Read via sudo so the api_key value is always available regardless
        # of the calling user's security group.
        rec = self.sudo()
        base_url = rec.api_base_url
        api_key = rec.api_key
        fetch_model_endpoint = rec.fetch_model_endpoint or '/v1/models'
        endpoint = base_url.rstrip('/') + '/' + fetch_model_endpoint.lstrip('/')

        try:
            headers = {}
            params = {}
            provider_name = (self.name or '').lower()
            base_url_lower = (self.api_base_url or '').lower()

            if 'openai' in provider_name or 'chatgpt' in provider_name or 'openai' in base_url_lower:
                headers['Authorization'] = 'Bearer %s' % api_key
            elif 'anthropic' in provider_name or 'anthropic' in base_url_lower:
                headers['x-api-key'] = api_key
                headers['anthropic-version'] = '2023-06-01'
            else:
                params = {'key': api_key}

            response = requests.get(endpoint, params=params, headers=headers, timeout=30)

            if response.status_code != 200:
                raise UserError(_('Error %s: %s') % (response.status_code, response.text))
            try:
                data = response.json()
            except ValueError:
                raise UserError(_('Invalid JSON response from the AI provider.'))
            if not isinstance(data, dict):
                raise UserError(_('Unexpected API response structure (not a dict).'))

            models_list = []
            if 'models' in data:
                models_list = data['models']
            elif 'data' in data and isinstance(data['data'], list):
                models_list = data['data']
            else:
                raise UserError(
                    _('Unexpected API response structure. Could not find a models list.')
                )

            if not models_list:
                raise UserError(_('No models returned by the provider.'))

            model_ids = []
            for record in models_list:
                # OpenAI uses 'id'; Gemini uses 'name'
                m_id = record.get('id') or record.get('name')
                if not m_id:
                    continue
                clean_id = m_id.replace('models/', '')

                existing_model = self.env['ai.model'].search(
                    [('model_ref_id', '=', clean_id)], limit=1
                )
                if existing_model:
                    model_ids.append(existing_model.id)
                else:
                    new_model = self.env['ai.model'].create({
                        'model_ref_id': clean_id,
                        'version': record.get('version', ''),
                        'display_label': record.get('displayName') or record.get('object', ''),
                        'owned_by': record.get('owned_by', ''),
                    })
                    model_ids.append(new_model.id)

            self.write({
                'ai_model_ids': [fields.Command.set(model_ids)]
            })

        except requests.exceptions.RequestException as e:
            raise UserError(_('Request failed: %s') % e)

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
from odoo import api, fields, models
from odoo.exceptions import UserError

from ..llm import ADAPTERS, LLMError


class AiAccountingProvider(models.Model):
    """An AI provider (Gemini, OpenAI, Claude, OpenRouter). Providers and
    their models are shared; API keys are personal (``ai.accounting.api.key``)."""
    _name = 'ai.accounting.provider'
    _description = 'AI Provider'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    provider_type = fields.Selection(
        selection=[
            ('gemini', 'Google Gemini'),
            ('openai', 'OpenAI (ChatGPT)'),
            ('anthropic', 'Anthropic (Claude)'),
            ('openrouter', 'OpenRouter'),
        ],
        string='Provider Type', required=True)
    base_url = fields.Char(
        string='Base URL',
        help="Leave empty to use the provider's official endpoint. For "
             "'OpenAI' you can point to any OpenAI-compatible endpoint.")
    model_ids = fields.One2many('ai.accounting.model', 'provider_id', string='Models')
    model_count = fields.Integer(compute='_compute_model_count')
    has_api_key = fields.Boolean(
        string='My API Key Set', compute='_compute_has_api_key',
        help="Whether you have saved your personal API key for this provider.")

    @api.depends('model_ids')
    def _compute_model_count(self):
        for provider in self:
            provider.model_count = len(provider.model_ids)

    @api.depends_context('uid')
    def _compute_has_api_key(self):
        keys = self.env['ai.accounting.api.key'].search([
            ('user_id', '=', self.env.uid), ('provider_id', 'in', self.ids)])
        with_key = keys.provider_id
        for provider in self:
            provider.has_api_key = provider in with_key

    # ------------------------------------------------------------------
    # Business
    # ------------------------------------------------------------------
    def _get_user_api_key(self):
        """API key of the current user for this provider."""
        self.ensure_one()
        key = self.env['ai.accounting.api.key'].search([
            ('user_id', '=', self.env.uid), ('provider_id', '=', self.id)], limit=1)
        secret = key.sudo().api_key
        if not secret:
            raise UserError(self.env._(
                "Add your personal API key for %s in Accounting > "
                "Configuration > AI Analytics > My API Keys.", self.name))
        return secret

    def _get_adapter(self, model=None, api_key=None, max_tokens=1024):
        self.ensure_one()
        return ADAPTERS[self.provider_type](
            api_key=api_key or self._get_user_api_key(),
            model=model.technical_name if model else '',
            base_url=self.base_url or None,
            max_tokens=max_tokens,
            extra_params=model._get_extra_params() if model else None,
        )

    def action_fetch_models(self):
        """Import the models available with the current user's API key.
        Prices are filled when the provider publishes them (OpenRouter)."""
        self.ensure_one()
        try:
            remote_models = self._get_adapter().list_models()
        except LLMError as error:
            raise UserError(self.env._("Could not fetch the models: %s", error)) from error
        existing = {model.technical_name: model for model in self.with_context(
            active_test=False).model_ids}
        to_create = []
        for remote in remote_models:
            prices = {key: remote[key] for key in ('price_input', 'price_output', 'price_cached')
                      if remote.get(key) is not None}
            model = existing.get(remote['technical_name'])
            if model:
                if prices:
                    model.write(prices)
            else:
                to_create.append({
                    'provider_id': self.id,
                    'name': remote['name'],
                    'technical_name': remote['technical_name'],
                    'active': False,
                    **prices,
                })
        self.env['ai.accounting.model'].create(to_create)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': self.env._(
                    "%(count)s new models imported (archived). Activate the ones "
                    "you want to offer and check their prices.", count=len(to_create)),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_view_models(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._("Models"),
            'res_model': 'ai.accounting.model',
            'view_mode': 'list,form',
            'domain': [('provider_id', '=', self.id)],
            'context': {'default_provider_id': self.id, 'active_test': False},
        }

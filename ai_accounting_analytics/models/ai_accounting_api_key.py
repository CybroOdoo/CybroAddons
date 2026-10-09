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
from odoo.exceptions import UserError, ValidationError

from ..llm import LLMError


class AiAccountingApiKey(models.Model):
    """Personal API key of a user for a provider. Access rules restrict each
    user to their own keys, and the key itself is never sent back to the
    browser: forms only write it (``new_api_key``) and show a masked hint."""
    _name = 'ai.accounting.api.key'
    _description = 'AI Provider API Key'
    _rec_name = 'provider_id'

    user_id = fields.Many2one('res.users', string='User', required=True, readonly=True,
                              default=lambda self: self.env.user, ondelete='cascade', index=True)
    provider_id = fields.Many2one('ai.accounting.provider', string='Provider',
                                  required=True, ondelete='cascade')
    model_id = fields.Many2one(
        'ai.accounting.model', string='Model', ondelete='set null',
        domain="[('provider_id', '=', provider_id)]",
        help="Your preferred model for this provider, preselected in AI Analytics.")
    # Restricted to system users so that no RPC (or injected script) can read
    # the secret back; the owner writes it through ``new_api_key`` and the
    # server reads it with ``sudo()`` on records the access rules let through.
    api_key = fields.Char(string='API Key', copy=False, groups='base.group_system')
    new_api_key = fields.Char(
        string='New API Key', compute='_compute_new_api_key', inverse='_inverse_new_api_key',
        help="Paste your key here. It is stored for your user only and never displayed again.")
    api_key_hint = fields.Char(string='Saved Key', compute='_compute_api_key_hint')

    _user_provider_uniq = models.Constraint(
        'UNIQUE(user_id, provider_id)', "You already have a key for this provider.")

    def _compute_new_api_key(self):
        for key in self:
            key.new_api_key = False

    def _inverse_new_api_key(self):
        for key in self:
            if key.new_api_key:
                key.sudo().api_key = key.new_api_key.strip()

    @api.onchange('provider_id')
    def _onchange_provider_id(self):
        if self.model_id.provider_id != self.provider_id:
            self.model_id = self.provider_id.model_ids[:1]

    @api.constrains('provider_id', 'model_id')
    def _check_model_provider(self):
        for key in self:
            if key.model_id and key.model_id.provider_id != key.provider_id:
                raise ValidationError(self.env._(
                    "The model %(model)s does not belong to %(provider)s.",
                    model=key.model_id.display_name, provider=key.provider_id.name))

    @api.depends('api_key')
    def _compute_api_key_hint(self):
        for key in self:
            secret = key.sudo().api_key or ''
            key.api_key_hint = '%s…%s' % (secret[:3], secret[-4:]) if len(secret) > 10 \
                else ('•' * len(secret))

    @api.model_create_multi
    def create(self, vals_list):
        if any(not vals.get('new_api_key') for vals in vals_list):
            raise UserError(self.env._("Please enter the API key."))
        return super().create(vals_list)

    def action_test_connection(self):
        """Check the key by listing the provider's models (no tokens used),
        and that the selected model is one of them."""
        self.ensure_one()
        try:
            models_found = self.provider_id._get_adapter(
                api_key=self.sudo().api_key).list_models()
        except LLMError as error:
            raise UserError(self.env._("Connection failed: %s", error)) from error
        available = {model['technical_name'] for model in models_found}
        if self.model_id and self.model_id.technical_name not in available:
            notification_type = 'warning'
            message = self.env._(
                "Connection successful, but %(model)s is not available to your key. "
                "Select another model, or use Fetch Models on the provider.",
                model=self.model_id.technical_name)
        else:
            notification_type = 'success'
            message = self.env._("Connection successful: %s models available.", len(models_found))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'type': notification_type, 'message': message},
        }

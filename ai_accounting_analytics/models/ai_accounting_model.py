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
import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AiAccountingModel(models.Model):
    """A model offered by a provider, with its prices (USD per million
    tokens) used to compute the cost of every call."""
    _name = 'ai.accounting.model'
    _description = 'AI Model'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    technical_name = fields.Char(
        required=True, help="Model identifier sent to the provider, e.g. gemini-3.5-flash-lite.")
    provider_id = fields.Many2one('ai.accounting.provider', string='Provider',
                                  required=True, ondelete='cascade', index=True)
    provider_type = fields.Selection(related='provider_id.provider_type')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    price_input = fields.Float(string='Input Price', digits=(16, 4),
                               help="USD per million uncached input tokens.")
    price_cached = fields.Float(string='Cached Input Price', digits=(16, 4),
                                help="USD per million input tokens read from the prompt cache.")
    price_cache_write = fields.Float(
        string='Cache Write Price', digits=(16, 4),
        help="USD per million input tokens written to the prompt cache "
             "(Claude only; leave 0 to use 1.25 x the input price).")
    price_output = fields.Float(string='Output Price', digits=(16, 4),
                                help="USD per million output tokens (reasoning included).")
    max_output_tokens = fields.Integer(
        help="Maximum tokens of one answer. 0 uses the general setting.")
    extra_params = fields.Text(
        string='Extra Request Parameters',
        help="Optional JSON merged into every request body, e.g. "
             '{"generationConfig": {"thinkingConfig": {"thinkingLevel": "low"}}} '
             'for Gemini or {"output_config": {"effort": "low"}} for Claude. '
             "Used to cut reasoning tokens.")

    _provider_technical_name_uniq = models.Constraint(
        'UNIQUE(provider_id, technical_name)',
        "This model already exists for the provider.")

    @api.depends('name', 'provider_id.name')
    def _compute_display_name(self):
        for model in self:
            model.display_name = '%s (%s)' % (model.name, model.provider_id.name) \
                if model.provider_id else model.name

    @api.constrains('extra_params')
    def _check_extra_params(self):
        for model in self:
            if not model.extra_params:
                continue
            try:
                value = json.loads(model.extra_params)
            except ValueError as error:
                raise ValidationError(self.env._(
                    "Extra Request Parameters must be valid JSON: %s", error)) from error
            if not isinstance(value, dict):
                raise ValidationError(self.env._(
                    "Extra Request Parameters must be a JSON object."))

    def _get_extra_params(self):
        self.ensure_one()
        return json.loads(self.extra_params) if self.extra_params else {}

    def _compute_cost(self, usage):
        """Cost in USD of one call (``llm.Usage``), unless the provider
        reported it."""
        self.ensure_one()
        if usage.cost is not None:
            return usage.cost
        cache_write_price = self.price_cache_write or self.price_input * 1.25
        return (usage.input_tokens * self.price_input
                + usage.cached_tokens * (self.price_cached or self.price_input)
                + usage.cache_write_tokens * cache_write_price
                + usage.output_tokens * self.price_output) / 1_000_000

# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import api, fields, models


class AiCustomProvider(models.Model):
    _name = 'ai.custom.provider'
    _description = 'AI Provider (OpenAI-compatible)'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    base_url = fields.Char(
        string="API Base URL", required=True,
        help="OpenAI-compatible base URL, without the trailing /chat/completions.",
    )
    api_key = fields.Char(string="API Key", groups='base.group_system', copy=False)
    send_embedding_dimensions = fields.Boolean(
        string="Send 'dimensions=1536'", default=True,
        help="Odoo stores 1536-dimension vectors. Disable for providers that reject the 'dimensions' parameter.",
    )
    model_ids = fields.One2many('ai.custom.provider.model', 'provider_id', string="Models", context={'active_test': False})
    chat_model_count = fields.Integer(compute='_compute_model_counts')
    embedding_model_count = fields.Integer(compute='_compute_model_counts')
    note = fields.Text()

    @api.depends('model_ids.model_type')
    def _compute_model_counts(self):
        for provider in self:
            provider.chat_model_count = len(provider.model_ids.filtered(lambda m: m.model_type == 'chat'))
            provider.embedding_model_count = len(provider.model_ids.filtered(lambda m: m.model_type == 'embedding'))


class AiCustomProviderModel(models.Model):
    _name = 'ai.custom.provider.model'
    _description = 'AI Provider Model'
    _order = 'provider_id, model_type, sequence, name'

    name = fields.Char(
        string="Model ID", required=True,
        help="Exact model identifier sent to the API, e.g. gpt-4.1-mini.",
    )
    label = fields.Char(help="Optional friendly name shown in dropdowns.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    provider_id = fields.Many2one('ai.custom.provider', required=True, ondelete='cascade', index=True)
    model_type = fields.Selection(
        [('chat', 'Chat'), ('embedding', 'Embedding')],
        string="Type", required=True, default='chat',
    )

    _name_provider_type_uniq = models.Constraint(
        'UNIQUE(provider_id, model_type, name)',
        "This model already exists for this provider.",
    )

    @api.depends('name', 'label')
    def _compute_display_name(self):
        for model in self:
            model.display_name = f"{model.label} ({model.name})" if model.label else model.name

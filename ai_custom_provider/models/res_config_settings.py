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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_custom_provider_enabled = fields.Boolean(
        string="Use Custom AI Provider",
        config_parameter='ai_custom_provider.enabled',
        help="Send Odoo AI requests to your own OpenAI-compatible endpoint instead of Odoo IAP.",
    )
    ai_custom_provider_id = fields.Many2one(
        'ai.custom.provider', string="Provider",
        config_parameter='ai_custom_provider.provider_id',
    )
    ai_custom_provider_base_url = fields.Char(
        related='ai_custom_provider_id.base_url', readonly=False,
    )
    ai_custom_provider_api_key = fields.Char(
        related='ai_custom_provider_id.api_key', readonly=False,
    )
    ai_custom_provider_send_embedding_dimensions = fields.Boolean(
        related='ai_custom_provider_id.send_embedding_dimensions', readonly=False,
    )
    ai_custom_provider_model_id = fields.Many2one(
        'ai.custom.provider.model', string="Chat Model",
        config_parameter='ai_custom_provider.model_id',
        domain="[('provider_id', '=', ai_custom_provider_id), ('model_type', '=', 'chat')]",
    )
    ai_custom_provider_reasoning_model_id = fields.Many2one(
        'ai.custom.provider.model', string="Reasoning Model",
        config_parameter='ai_custom_provider.reasoning_model_id',
        domain="[('provider_id', '=', ai_custom_provider_id), ('model_type', '=', 'chat')]",
        help="Used when 'Think longer' is enabled. Leave empty to use the chat model.",
    )
    ai_custom_provider_embedding_model_id = fields.Many2one(
        'ai.custom.provider.model', string="Embedding Model",
        config_parameter='ai_custom_provider.embedding_model_id',
        domain="[('provider_id', '=', ai_custom_provider_id), ('model_type', '=', 'embedding')]",
        help="Must produce 1536-dimension vectors. Leave empty if the provider has no compatible embedding model "
             "(AI agents will then not use document sources).",
    )
    ai_custom_provider_timeout = fields.Integer(
        string="Timeout (s)",
        config_parameter='ai_custom_provider.timeout',
        default=120,
    )

    def set_values(self):
        ICP = self.env['ir.config_parameter'].sudo()
        old_embedding = (ICP.get_bool('ai_custom_provider.enabled'), ICP.get_int('ai_custom_provider.embedding_model_id'))
        super().set_values()
        new_embedding = (ICP.get_bool('ai_custom_provider.enabled'), ICP.get_int('ai_custom_provider.embedding_model_id'))
        if old_embedding != new_embedding:
            # Re-embed agent sources with the newly selected embedding model.
            self.env.ref('ai.ir_cron_update_deprecated_embedding_models')._trigger()

    @api.onchange('ai_custom_provider_id')
    def _onchange_ai_custom_provider_id(self):
        """Pick the provider's first models when switching provider."""
        provider = self.ai_custom_provider_id
        for field_name, model_type in (
            ('ai_custom_provider_model_id', 'chat'),
            ('ai_custom_provider_embedding_model_id', 'embedding'),
        ):
            if self[field_name].provider_id != provider:
                self[field_name] = provider.model_ids.filtered(lambda m: m.model_type == model_type)[:1]
        if self.ai_custom_provider_reasoning_model_id.provider_id != provider:
            self.ai_custom_provider_reasoning_model_id = False

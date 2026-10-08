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
from odoo import api, models
from odoo.exceptions import UserError

from ..utils.openai_client import ProviderError, get_embeddings, get_provider_config


class AiEmbedding(models.Model):
    _inherit = 'ai.embedding'

    @api.model
    def _get_default_embedding_model(self):
        config = get_provider_config(self.env)
        if not config['enabled'] or not config['embedding_model']:
            return super()._get_default_embedding_model()
        return config['embedding_model']

    @api.model
    def _get_supported_embedding_models(self):
        # Embeddings made with another model (e.g. by Odoo's IAP) are re-computed
        # by the "deprecated embedding models" cron.
        config = get_provider_config(self.env)
        if not config['enabled'] or not config['embedding_model']:
            return super()._get_supported_embedding_models()
        return [config['embedding_model']]

    @api.model
    def _get_embeddings(self, input, model, mode):
        config = get_provider_config(self.env)
        if not config['enabled']:
            return super()._get_embeddings(input, model, mode)
        try:
            # Always use the configured model: stored embeddings may come from another provider.
            return get_embeddings(config, input, model=config['embedding_model'])
        except ProviderError as e:
            raise UserError(str(e)) from e

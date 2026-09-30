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

from odoo import api, models


class OcrAiSaleOrder(models.Model):
    """Extends sale.order with OCR AI tracking fields."""
    _name = 'sale.order'
    _inherit = ['sale.order', 'odoo.ocr.ai.mixin']

    @api.model_create_multi
    def create(self, vals_list):
        """Link the OCR attachment to the newly created sale order."""
        records = super().create(vals_list)
        for record in records:
            if record.is_created_ocr and record.ocr_attachment_id:
                record.ocr_attachment_id.sudo().write({
                    'res_id': record.id,
                    'res_model': self._name,
                })
        return records

    @api.model
    def check_active_ocr_config(self, active_model, *args):
        """Called by JS to check if an active OCR config exists for this model."""
        config = self.env['odoo.ocr.ai.config'].search([
            ('active', '=', True),
            ('model_id.model', '=', active_model),
        ], limit=1)
        if config:
            return {'active': True, 'record_id': config.id}
        return {'active': False}
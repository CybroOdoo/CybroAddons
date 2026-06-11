# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
_logger = logging.getLogger(__name__)

from odoo import fields, models,api


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    tab_id = fields.Char(string='Tab ID')

    @api.model_create_multi
    def create(self, vals_list):
        """Capture tab_id from context at wizard creation time."""
        ctx_tab_id = self.env.context.get('tab_id', '') or self.env.context.get('default_tab_id', '')
        for vals in vals_list:
            if not vals.get('tab_id') and ctx_tab_id:
                vals['tab_id'] = ctx_tab_id
        return super().create(vals_list)

    def process(self):
        self.ensure_one()
        action = super().process()

        if not action or not isinstance(action, dict):
            return action

        if action.get('type') != 'ir.actions.report' or action.get('report_type') != 'qweb-pdf':
            return action

        report_name = action.get('report_name')

        # The 'data' dict contains quantity_by_product, layout_wizard, active_model etc.
        # It is REQUIRED for product label reports — must be passed to _render_qweb_pdf
        report_data = action.get('data') or {}
        
        # Standardize quantity_by_product keys to strings (Odoo expects strings for product IDs in the data dict)
        if 'quantity_by_product' in report_data:
            qty_by_product = report_data['quantity_by_product']
            report_data['quantity_by_product'] = {str(k): v for k, v in qty_by_product.items()}

        # docids: prioritize wizard fields over context active_ids
        docids = []
        if hasattr(self, 'product_tmpl_ids') and self.product_tmpl_ids:
            docids = self.product_tmpl_ids.ids
        elif hasattr(self, 'product_ids') and self.product_ids:
            docids = self.product_ids.ids
        
        if not docids:
            docids = (
                action.get('docids')
                or action.get('context', {}).get('active_ids')
                or ([action['context']['active_id']] if action.get('context', {}).get('active_id') else [])
                or self.env.context.get('active_ids', [])
                or ([self.env.context['active_id']] if self.env.context.get('active_id') else [])
            )

        # tab_id: prefer wizard field, then context
        tab_id = (
            self.tab_id
            or self.env.context.get('tab_id')
            or self.env.context.get('default_tab_id')
            or ''
        )

        _logger.info(
            "ProductLabelLayout.process: report=%s docids=%s tab_id='%s' data_keys=%s",
            report_name, docids, tab_id, list(report_data.keys())
        )

        if not report_name or not docids:
            _logger.warning("Missing report_name or docids — falling back to original action")
            return action

        if not tab_id:
            _logger.warning("tab_id is empty — PDF will generate but may not download to correct tab")

        try:
            self.env['ir.actions.report'].generate_in_background(
                report_name=report_name,
                docids=list(docids),
                data=report_data,
                tab_id=tab_id,
                context=dict(self.env.context),
            )
        except Exception as e:
            _logger.exception("generate_in_background() failed: %s", e)
            return action

        return {'type': 'ir.actions.act_window_close'}
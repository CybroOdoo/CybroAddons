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
from odoo import api, models

_logger = logging.getLogger(__name__)

POS_RELEVANT_FIELDS = {
    'name',
    'list_price',
    'lst_price',
    'standard_price',
    'barcode',
    'default_code',
    'categ_id',
    'pos_categ_ids',
    'taxes_id',
    'active',
    'available_in_pos',
}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        """Pass the Bus notification once when new product templates are created."""
        records = super(ProductTemplate, self.with_context(skip_pos_notify=True)).create(vals_list)
        variants = records.product_variant_ids.filtered(lambda v: v.available_in_pos and v.active)
        if variants:
            pos_sessions = self.env['pos.session'].sudo().search([('state', '=', 'opened')])
            if pos_sessions:
                for variant in variants:
                    self.sudo()._notify_pos_product_change(variant, pos_sessions)
        return records.with_env(self.env)

    def write(self, vals):
        """Pass the bus notification when existing product templates are updated."""
        res = super(ProductTemplate, self.with_context(skip_pos_notify=True)).write(vals)
        if not any(f in vals for f in POS_RELEVANT_FIELDS):
            return res
        pos_sessions = self.env['pos.session'].sudo().search([('state', '=', 'opened')])
        if not pos_sessions:
            return res

        if 'active' in vals or 'available_in_pos' in vals:
            variants = self.with_context(active_test=False).mapped("product_variant_ids")
        else:
            variants = self.mapped("product_variant_ids").filtered(lambda v: v.available_in_pos and v.active)

        if variants:
            for variant in variants:
                self.sudo()._notify_pos_product_change(variant, pos_sessions)
        return res

    def _notify_pos_product_change(self, product, pos_sessions_or_configs):
        """Send bus notification to all active POS sessions via their config bus mixin."""
        product = product.sudo()
        notification_data = {
            'product_id': int(product.id),
            'product_tmpl_id': int(product.product_tmpl_id.id),
            'name': str(product.display_name),
            'tmpl_name': str(product.product_tmpl_id.name),
            'list_price': float(product.lst_price),
            'standard_price': float(product.standard_price),
            'qty_available': float(product.qty_available),
            'barcode': str(product.barcode or ""),
            'default_code': str(product.default_code or ""),
            'categ_id': int(product.categ_id.id) if product.categ_id else False,
            'taxes_id': [int(t) for t in product.taxes_id.ids],
            'active': bool(product.active and product.product_tmpl_id.active),
            'tmpl_active': bool(product.product_tmpl_id.active),
            'available_in_pos': bool(product.available_in_pos and product.product_tmpl_id.available_in_pos),
        }
        if pos_sessions_or_configs._name == 'pos.session':
            configs = pos_sessions_or_configs.sudo().mapped('config_id')
        else:
            configs = pos_sessions_or_configs.sudo()

        for config in configs:
            try:
                config.sudo()._notify("PRODUCT_UPDATE", notification_data)
            except Exception:
                _logger.exception(
                    "pos_update_realtime: failed to send PRODUCT_UPDATE "
                    "notification to POS config %s", config.id
                )


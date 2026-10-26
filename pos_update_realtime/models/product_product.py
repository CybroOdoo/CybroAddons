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
from odoo import api, models

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


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        """Pass the Bus notification when new product variants are created directly."""
        records = super().create(vals_list)
        if self.env.context.get('skip_pos_notify'):
            return records
        variants = records.filtered(lambda v: v.available_in_pos and v.active)
        if variants:
            pos_sessions = self.env['pos.session'].sudo().search([('state', '=', 'opened')])
            if pos_sessions:
                template_model = self.env['product.template'].sudo()
                for variant in variants:
                    template_model._notify_pos_product_change(variant, pos_sessions)
        return records

    def write(self, vals):
        """Pass the bus notification when product variants are directly updated."""
        res = super().write(vals)
        if self.env.context.get('skip_pos_notify'):
            return res
        if not any(f in vals for f in POS_RELEVANT_FIELDS):
            return res
        pos_sessions = self.env['pos.session'].sudo().search([('state', '=', 'opened')])
        if not pos_sessions:
            return res

        if 'active' in vals or 'available_in_pos' in vals:
            variants = self.with_context(active_test=False)
        else:
            variants = self.filtered(lambda v: v.available_in_pos and v.active)

        if variants:
            template_model = self.env['product.template'].sudo()
            for variant in variants:
                template_model._notify_pos_product_change(variant, pos_sessions)
        return res


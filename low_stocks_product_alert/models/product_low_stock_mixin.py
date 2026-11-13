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
from odoo import api, fields, models


class ProductLowStockAlertMixin(models.AbstractModel):
    """
    Abstract mixin model to provide common low stock alert logic for
    product.template and product.product.
    """
    _name = 'product.low.stock.alert.mixin'
    _description = 'Product Low Stock Alert Mixin'

    alert_tag = fields.Char(
        string='Product Alert Tag',
        compute='_compute_alert_state',
        help='This field represents the alert tag of the product.')
    alert_state = fields.Boolean(
        string='Product Alert State',
        compute='_compute_alert_state',
        help='This field represents the alert state of the product.')

    @api.depends('qty_available', 'type', 'is_storable')
    def _compute_alert_state(self):
        """Compute the alert state and alert tag based on the low stock configuration."""
        ir_config = self.env['ir.config_parameter'].sudo()
        val = ir_config.get_str('low_stocks_product_alert.is_low_stock_alert', default='False') or ''
        stock_alert = val.strip().lower() in ('true', '1')
        try:
            limit = float(ir_config.get_str('low_stocks_product_alert.min_low_stock_alert', default='0') or 0)
        except (ValueError, TypeError):
            limit = 0.0

        for rec in self:
            if stock_alert:
                rec.alert_state = bool(rec.is_storable and rec.qty_available <= limit)
                if rec.alert_state:
                    qty = int(rec.qty_available) if rec.qty_available % 1 == 0 else rec.qty_available
                    rec.alert_tag = str(qty)
                else:
                    rec.alert_tag = False
            else:
                rec.alert_state = False
                rec.alert_tag = False

    @api.model
    def _load_pos_data_fields(self, config_id=None, **kwargs):
        """Load additional low stock alert fields into the POS."""
        if hasattr(super(), '_load_pos_data_fields'):
            result = super()._load_pos_data_fields(config_id, **kwargs)
        else:
            result = []
        if isinstance(result, set):
            result.update({'alert_tag', 'alert_state'})
            return list(result)
        for field in ('alert_tag', 'alert_state'):
            if field not in result:
                result.append(field)
        return result

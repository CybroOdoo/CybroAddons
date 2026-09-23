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


class ProductTemplate(models.Model):
    """
    This is an Odoo model for product templates. It inherits from the
    'product.template' model and extends its functionality by adding computed
    fields for product alert state and color field.

    Methods:
         _compute_alert_state: Computes the 'alert_state' and 'color_field'
         fields based on the product's stock quantity and low stock
    alert parameters

    """
    _inherit = 'product.template'

    alert_tag = fields.Char(
        string='Product Alert Tag',
        compute='_compute_alert_state',
        help='This field represents the alert tag of the product.')
    alert_state = fields.Boolean(
        string='Product Alert State',
        compute='_compute_alert_state',
        help='This field represents the alert state of the product.')
    color_field = fields.Char(
        string='Background color',
        compute='_compute_alert_state',
        help='This field represents the background color of the product.')

    @api.depends('qty_available', 'type', 'is_storable')
    def _compute_alert_state(self):
        """Compute the alert state, background color and alert tag."""
        ir_config = self.env['ir.config_parameter'].sudo()
        if hasattr(ir_config, 'get_bool'):
            stock_alert = ir_config.get_bool('low_stocks_product_alert.is_low_stock_alert', default=False)
            limit = ir_config.get_int('low_stocks_product_alert.min_low_stock_alert', default=0)
        else:
            stock_alert = bool(ir_config.get_param('low_stocks_product_alert.is_low_stock_alert'))
            limit = int(ir_config.get_param('low_stocks_product_alert.min_low_stock_alert', default='0'))

        for rec in self:
            if stock_alert:
                rec.alert_state = bool(rec.is_storable and rec.qty_available <= limit)
                rec.color_field = '#fdc6c673' if rec.alert_state else 'white'
                if rec.alert_state:
                    qty = int(rec.qty_available) if rec.qty_available % 1 == 0 else rec.qty_available
                    rec.alert_tag = str(qty)
                else:
                    rec.alert_tag = False
            else:
                rec.alert_state = False
                rec.color_field = 'white'
                rec.alert_tag = False

    @api.model
    def _load_pos_data_fields(self, config_id):
        """This method is used to load additional fields in the POS"""
        result = super()._load_pos_data_fields(config_id)
        result.extend(['alert_tag', 'alert_state', 'color_field'])
        return result


# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ProductProduct(models.Model):
    """
    This is an Odoo model for product products. It inherits from the
    'product.product' model and extends its functionality by adding a
    computed field for product alert state.

     Methods:
        _compute_alert_tag(): Computes the value of the 'alert_tag' field based on the
        product's stock quantity and configured low stock alert parameters
    """
    _inherit = 'product.product'

    alert_tag = fields.Char(
        string='Product Alert Tag', compute='_compute_alert_tag',
        help='This field represents the alert tag of the product.')

    @api.depends('qty_available')
    def _compute_alert_tag(self):
        """Compute the alert tag based on the low stock configuration."""
        ir_config = self.env['ir.config_parameter'].sudo()
        stock_alert = ir_config.get_param(
            'low_stocks_product_alert.is_low_stock_alert')
        limit = int(
            ir_config.get_param(
                'low_stocks_product_alert.min_low_stock_alert',
                default='0'))
        for rec in self:
            if stock_alert:
                is_low_stock = rec.is_storable and rec.qty_available <= limit
                rec.alert_tag = str(rec.qty_available) if is_low_stock else False
            else:
                rec.alert_tag = False


    alert_state = fields.Boolean(string='Product Alert State',
                                 compute='_compute_alert_state',
                                 help='This field represents the alert state'
                                      'of the product')
    color_field = fields.Char(string='Background color',
                              help='This field represents the background '
                                   'color of the product.')

    @api.depends('qty_available')
    def _compute_alert_state(self):
        """Compute the alert state and background color."""
        ir_config = self.env['ir.config_parameter'].sudo()
        stock_alert = ir_config.get_param(
            'low_stocks_product_alert.is_low_stock_alert')
        limit = int(
            ir_config.get_param(
                'low_stocks_product_alert.min_low_stock_alert',
                default='0'))

        for rec in self:
            if stock_alert:
                rec.alert_state = (rec.is_storable and rec.qty_available <= limit)
                rec.color_field = ( '#fdc6c673' if rec.alert_state else 'white')
            else:
                rec.alert_state = False
                rec.color_field = 'white'

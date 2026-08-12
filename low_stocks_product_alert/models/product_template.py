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
        help='This field represents the alert tag of the product.', compute='_compute_alert_state')

    alert_state = fields.Boolean(string='Product Alert State',
                                 compute='_compute_alert_state',
                                 help='This field represents the alert state'
                                      'of the product')
    color_field = fields.Char(string='Background color',
                              help='This field represents the background '
                                   'color of the product.')

    @api.depends('qty_available')
    def _compute_alert_state(self):
        """Compute the alert state, background color and alert tag."""
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
                rec.color_field = ('#fdc6c673' if rec.alert_state else 'white')
                rec.alert_tag = (str(rec.qty_available) if rec.alert_state else False)
            else:
                rec.alert_state = False
                rec.color_field = 'white'
                rec.alert_tag = False

    @api.model
    def _load_pos_data_fields(self, config_id):
        """This method is used to load additional fields in the POS"""
        result = super()._load_pos_data_fields(config_id)
        result.append('alert_tag')
        return result

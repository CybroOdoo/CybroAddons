# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    is_low_stock_alert = fields.Boolean(string="Low Stock Alert")
    min_low_stock_alert = fields.Integer(
        string='Alert Quantity', default=0,
        help='Change the background color for the product based'
             ' on the Alert Quant.')

    def set_values(self):
        super(ResConfig, self).set_values()

        self.env['ir.config_parameter'].set_param(
            'product_stock_alert.is_low_stock_alert', self.is_low_stock_alert)

        self.env['ir.config_parameter'].set_param(
            'product_stock_alert.min_low_stock_alert', self.min_low_stock_alert)

    @api.model
    def get_values(self):
        res = super(ResConfig, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            is_low_stock_alert=params.get_param(
                'product_stock_alert.is_low_stock_alert'),
            min_low_stock_alert=params.get_param(
                'product_stock_alert.min_low_stock_alert'),
        )
        return res

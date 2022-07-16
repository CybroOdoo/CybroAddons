# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'product template'

    alert_state = fields.Boolean(string='Product Alert State', default=False,
                                 compute='_compute_alert_state')
    color_field = fields.Char(string='Background color')

    @api.depends('qty_available')
    def _compute_alert_state(self):
        is_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'product_stock_alert.is_low_stock_alert')
        min_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'product_stock_alert.min_low_stock_alert')
        if is_low_stock_alert:
            for rec in self:
                rec.alert_state = False
                rec.color_field = 'white'
                if rec.type == 'product':
                    if rec.qty_available <= int(min_low_stock_alert):
                        rec.alert_state = True
                        rec.color_field = '#fdc6c673'

        else:
            self.alert_state = False
            self.color_field = 'white'


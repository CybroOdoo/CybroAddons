# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    alert_tag = fields.Char(
        string='Product Alert State', compute='_compute_alert_tag')

    @api.depends('qty_available')
    def _compute_alert_tag(self):
        is_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'product_stock_alert.is_low_stock_alert')
        min_low_stock_alert = self.env[
            'ir.config_parameter'].sudo().get_param(
            'product_stock_alert.min_low_stock_alert')
        if is_low_stock_alert:
            for rec in self:
                rec.alert_tag = False
                if rec.type == 'product':
                    if rec.qty_available <= int(min_low_stock_alert):
                        rec.alert_tag = rec.qty_available

        else:
            self.alert_tag = False





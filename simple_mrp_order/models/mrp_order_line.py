# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MRPOrderLine(models.Model):
    _name = 'mrp.order.line'
    _description = "Bills of Materials Components"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_qty = fields.Float(string="Quantity", default=1.0, tracking=True)
    uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', required=True)
    mrp_id = fields.Many2one('mrp.order')


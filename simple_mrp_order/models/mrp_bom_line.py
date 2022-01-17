# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SimpleMRPBomLine(models.Model):
    _name = 'simple.mrp.bom.line'
    _description = "Bills of Materials Components"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_qty = fields.Float(string="Quantity", default=1.0, tracking=True)
    uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', required=True)
    bom_id = fields.Many2one('simple.mrp.bom')


    @api.onchange('product_id')
    def onchange_product_id(self):
        """ Update the Uom for the product """
        self.uom_id = self.product_id.uom_id.id
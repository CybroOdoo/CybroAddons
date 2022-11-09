# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SimpleMRPBom(models.Model):
    _name = 'simple.mrp.bom'
    _description = "Bills of Materials"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_qty = fields.Float(string="Quantity", default=1.0, tracking=True)
    uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,
                                 index=True, required=True)
    # mrp_id = fields.Many2one('mrp.order', string="Manufacturing Order")
    line_ids = fields.One2many('simple.mrp.bom.line', 'bom_id', string="Components")

    @api.onchange('product_id')
    def onchange_product_id(self):
        """ Update the Uom for the product """
        self.uom_id = self.product_id.uom_id.id



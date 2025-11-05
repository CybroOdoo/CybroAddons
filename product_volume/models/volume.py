# -*- coding: utf-8 -*-

from odoo import api, models, fields

class ProductDimensionsVolume(models.Model):
    _inherit = 'product.template'

    length = fields.Char(string="Length")
    breadth = fields.Char(string="Breadth")
    height = fields.Char(string="Height")

    @api.onchange('length','breadth','height')
    def onchange_l_b_h(self):
        self.volume = float(self.length if self.length else 0) * float(self.breadth if self.breadth else 0) * float(self.height if self.height else 0)

# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    barcode = fields.Char(string='Barcode')

    @api.onchange('barcode')
    def barcode_scrap(self):
        if self.barcode:
            if not self.product_id:
                product = self.env['product.product'].search([('barcode', '=', self.barcode)])
                if product:
                    if self.barcode == product.barcode:
                        self.product_id = product.id
                        if not self.scrap_qty == 1:
                            self.scrap_qty += 1
                        self.barcode = None
                else:
                    self.barcode = None
                    raise Warning('There is no product available for this barcode.'
                                  'Please check you scanned the correct one')
            else:
                if self.barcode == self.product_id.barcode:
                    self.scrap_qty += 1
                    self.barcode = None
                else:
                    self.barcode = None
                    raise Warning('You sure about the product.!'
                                  'Please check you scanned the correct one')

# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import Warning


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    barcode = fields.Char(string='Barcode')

    @api.onchange('barcode')
    def barcode_scanning(self):
        match = False
        product_obj = self.env['product.product']
        product_id = product_obj.search([('barcode', '=', self.barcode)])
        if self.barcode and not product_id:
            raise Warning('No product is available for this barcode')
        if self.barcode and self.move_ids_without_package:
            for line in self.move_ids_without_package:
                if line.product_id.barcode == self.barcode:
                    line.quantity_done += 1
                    match = True
        if self.barcode and not match:
            if product_id:
                raise Warning('This product is not available in the order.'
                              'You can add this product by clicking the "Add an item" and scan')

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if vals.get('barcode') and self.move_ids_without_package:
            for line in self.move_ids_without_package:
                if line.product_id.barcode == vals['barcode']:
                    print(line.quantity_done)
                    line.quantity_done += 1
                    self.barcode = None
        return res


class StockPickingOperation(models.Model):
    _inherit = 'stock.move'

    barcode = fields.Char(string='Barcode')

    @api.onchange('barcode')
    def _onchange_barcode_scan(self):
        product_rec = self.env['product.product']
        if self.barcode:
            product = product_rec.search([('barcode', '=', self.barcode)])
            self.product_id = product.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

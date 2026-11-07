#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class StockMove(models.Model):
    """Inherits Stock move for scanning multi barcode"""
    _inherit = 'stock.move'

    scan_barcode = fields.Char(
        string='Product Barcode',
        compute='_compute_scan_barcode',
        store=True,
        readonly=False,
        help="Here you can provide the barcode for the product",
    )

    @api.depends('sale_line_id', 'purchase_line_id')
    def _compute_scan_barcode(self):
        """For updating the Product Barcode field in delivery while it's
        generating from a Purchase order or sale order"""
        for stock in self:
            if hasattr(stock, 'sale_line_id') and stock.sale_line_id:
                stock.scan_barcode = stock.sale_line_id.scan_barcode
            elif hasattr(stock, 'purchase_line_id') and stock.purchase_line_id:
                stock.scan_barcode = stock.purchase_line_id.scan_barcode
            elif not stock.scan_barcode:
                stock.scan_barcode = False

    @api.onchange('scan_barcode')
    def _onchange_scan_barcode(self):
        """For getting the scanned barcode product"""
        if not self.scan_barcode:
            return None
        product = self.env['product.multiple.barcodes'].find_product_by_barcode(self.scan_barcode)
        if not product:
            return {
                'warning': {
                    'title': self.env._('Barcode Not Found'),
                    'message': self.env._(
                        'No product found for barcode "%(barcode)s".',
                        barcode=self.scan_barcode,
                    ),
                },
            }
        self.product_id = product.id
        if hasattr(self, '_onchange_product_id'):
            self._onchange_product_id()
        if hasattr(self, 'description_picking') and not self.description_picking:
            self.description_picking = product.display_name
        elif hasattr(self, 'name') and not self.name:
            self.name = product.display_name
        return None

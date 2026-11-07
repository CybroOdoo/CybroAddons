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


class SaleOrderLine(models.Model):
    """Inherits Sale order line for scanning multi barcode"""
    _inherit = 'sale.order.line'

    scan_barcode = fields.Char(
        string='Product Barcode',
        help="Here you can provide the barcode for the product",
    )

    def _prepare_invoice_line(self, **optional_values):
        """For adding the scanned barcode in the invoice"""
        res = super()._prepare_invoice_line(**optional_values)
        scan_barcode = False
        if hasattr(self, 'move_ids') and self.move_ids:
            scan_barcode = self.move_ids[:1].scan_barcode
        res['scan_barcode'] = scan_barcode or self.scan_barcode
        return res

    @api.onchange('scan_barcode')
    def _onchange_scan_barcode(self):
        """Lookup multi-barcode or standard barcode and set product + description."""
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
        # In Odoo 20, sale.order.line uses product_template_id and product_id
        self.product_template_id = product.product_tmpl_id.id
        self.product_id = product.id
        if hasattr(self, '_onchange_product_id'):
            self._onchange_product_id()
        if hasattr(self, '_compute_product_template_id'):
            self._compute_product_template_id()
        if hasattr(self, '_compute_name'):
            self._compute_name()
        if not self.name:
            self.name = product.description_sale or product.display_name
        if hasattr(self, '_compute_label'):
            self._compute_label()
        if not self.product_uom_qty:
            self.product_uom_qty = 1.0
        return None

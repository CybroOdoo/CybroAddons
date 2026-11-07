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


class PurchaseOrderLines(models.Model):
    """Inherits Purchase order line for scanning multi barcode"""
    _inherit = 'purchase.order.line'

    scan_barcode = fields.Char(
        string='Product Barcode',
        help="Here you can provide the barcode for the product",
    )

    @api.onchange('scan_barcode')
    def _onchange_scan_barcode(self):
        """Lookup multi-barcode or standard barcode and set product + description on purchase line."""
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
        if hasattr(self, '_product_id_change'):
            self._product_id_change()
        if hasattr(self, '_suggest_quantity'):
            self._suggest_quantity()
        if not self.name:
            self.name = product.description_purchase or product.display_name
        if hasattr(self, '_compute_label'):
            self._compute_label()
        return None

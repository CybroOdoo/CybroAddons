# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class StockMove(models.Model):
    """Extends the Stock Move model to add a new field for scanning barcodes."""

    _inherit = 'stock.move'

    scan_barcode = fields.Char(string='Product Barcode',
                               help="Scan the barcode of the product to"
                                    " automatically set its ID.")

    @api.onchange('scan_barcode')
    def _onchange_scan_barcode(self):
        """Updates the product_id field when a barcode is scanned.

        This method searches for a product with the scanned barcode using the
        product.multiple.barcodes model, and sets the product_id field to the
        product_barcode_id of the matching product.

        """
        if self.scan_barcode:
            self.product_id = self.env['product.multiple.barcodes'].search(
                [('product_multi_barcode', '=',
                  self.scan_barcode)]).product_barcode_id

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


class PurchaseOrderLines(models.Model):
    _inherit = "purchase.order.line"
    """
    This model inherits 'purchase.order.line' model to extend its functionality 
    with a new field 'scan_barcode'.
    """

    scan_barcode = fields.Char(string='Product Barcode',
                               help="Here you can provide the barcode for the "
                                    "product")

    @api.onchange('scan_barcode')
    def _onchange_scan_barcode(self):
        """
        This function is called when the 'scan_barcode' field is changed. It
        searches for the product with the scanned barcode in the
        'product.multiple.barcodes' model and sets the 'product_id' field
        of the current record to the found product.
        """
        if self.scan_barcode:
            self.product_id = self.env['product.multiple.barcodes'].search(
                [('product_multi_barcode', '=',
                  self.scan_barcode)]).product_barcode_id

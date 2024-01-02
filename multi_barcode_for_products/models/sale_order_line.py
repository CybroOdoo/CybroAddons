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


class SaleOrderLines(models.Model):
    """
    This class is used to inherit Sale Order Line and add a new field
    "scan_barcode" which can be used to scan the barcode of a product and
    set the corresponding product in the sale order line.
    """
    _inherit = 'sale.order.line'

    scan_barcode = fields.Char(string='Product Barcode',
                               help="Enter the barcode for the product to "
                                    "add it to the sale order line")

    @api.onchange('scan_barcode')
    def _onchange_scan_barcode(self):
        """
        This method is triggered when the value of the "scan_barcode" field
        changes. It searches the product with the given barcode in the
        "product.multiple.barcodes" model and sets the corresponding product in
        the sale order line.
        """
        if self.scan_barcode:
            self.product_id = self.env['product.multiple.barcodes'].search(
                [('product_multi_barcode', '=',
                  self.scan_barcode)]).product_barcode_id

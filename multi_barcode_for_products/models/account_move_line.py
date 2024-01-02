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


class AccountMoveLine(models.Model):
    """Inherits Invoice Lines

    This model inherits from the `account.move.line` model and adds a new
    field `scan_barcode` for scanning product barcodes. The `_onchange_scan
    _barcode`    method is triggered whenever the `scan_barcode` field is
    changed, and it    searches for a `product.multiple.barcodes` record
    that matches the scanned barcode. If a matching record is found, it sets
    the `product_id` field to the corresponding product barcode ID.

    Attributes:
        _inherit (str): Name of the parent model to inherit from.
        scan_barcode (fields.Char): Field for scanning product barcodes.
    """

    _inherit = 'account.move.line'

    scan_barcode = fields.Char(string='Product Barcode',
                               help="You can scan the barcode here")

    @api.onchange('scan_barcode')
    def _onchange_scan_barcode(self):
        """For getting the scanned barcode product
        This method is triggered whenever the `scan_barcode` field is changed.
        It searches for a `product.multiple.barcodes` record that matches the
        scanned barcode. If a matching record is found, it sets the
        `product_id` field to the corresponding product barcode ID.
        """
        if self.scan_barcode:
            self.product_id = self.env['product.multiple.barcodes'].search(
                [('product_multi_barcode', '=',
                  self.scan_barcode)]).product_barcode_id

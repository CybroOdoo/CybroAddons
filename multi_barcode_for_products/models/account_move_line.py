# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ADVAITH B G (odoo@cybrosys.com)
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
    """Inherits Account move line for scanning multi barcode"""
    _inherit = 'account.move.line'

    scan_barcode = fields.Char(string='Product Barcode',
                               compute="_compute_scan_barcode",
                               inverse="_inverse_scan_barcode", store=True,
                               help="You can scan the barcode here")

    @api.depends('purchase_line_id')
    def _compute_scan_barcode(self):
        """For updating the Product Barcode field in move line while it's
        generating from a Purchase order"""
        for line in self:
            if line.purchase_line_id:
                line.scan_barcode = line.purchase_line_id.scan_barcode

    def _inverse_scan_barcode(self):
        """Inverse function for scan_barcode"""
        for account in self:
            account.scan_barcode = account.scan_barcode

    @api.onchange('scan_barcode')
    def _onchange_scan_barcode(self):
        """For getting the scanned barcode product"""
        if self.scan_barcode:
            product = self.env['product.multiple.barcodes'].search(
                [('product_multi_barcode', '=', self.scan_barcode)])
            self.product_id = product.product_id.id

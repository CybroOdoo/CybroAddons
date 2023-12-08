# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
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
    """Inherited the model for to add field for barcode."""
    _inherit = 'account.move.line'

    barcode_scan = fields.Char(string='Product Barcode',
                               related='product_id.barcode', readonly=False,
                               help="Here you can provide the barcode for "
                                    "the product")

    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        """Onchange function for searching product using their barcode"""
        if self.barcode_scan:
            self.product_id = self.env['product.product'].search(
                [('barcode', '=', self.barcode_scan)])

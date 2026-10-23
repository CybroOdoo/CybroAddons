# -*- coding: utf-8 -*-
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

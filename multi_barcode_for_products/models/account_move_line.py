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
    """ Inherits Account.move.line for scanning multi barcode """
    _inherit = 'account.move.line'

    scan_barcode = fields.Char(
        string='Product Barcode',
        compute="_compute_scan_barcode",
        store=True,
        readonly=False,
        help="You can scan the barcode here",
    )

    @api.depends('purchase_line_id')
    def _compute_scan_barcode(self):
        """ For updating the Product Barcode field in move line while it's
        generating from a Purchase order. """
        for line in self:
            if hasattr(line, 'purchase_line_id') and line.purchase_line_id:
                line.scan_barcode = line.purchase_line_id.scan_barcode
            elif not line.scan_barcode:
                line.scan_barcode = False

    @api.onchange('scan_barcode')
    def _onchange_scan_barcode(self):
        """Lookup multi-barcode or standard barcode and set product + description on invoice line."""
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
        if not self.name:
            self.name = product.description_sale or product.display_name
        return None

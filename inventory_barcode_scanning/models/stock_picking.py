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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    """Inherit stock_picking to add barcode scanning capability"""
    _inherit = 'stock.picking'

    barcode = fields.Char(help="Barcode for Scanning Product")

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Function to add product line or increment quantity when entering a Barcode."""
        if not self.barcode:
            return

        product_id = self.env['product.product'].search(
            [('barcode', '=', self.barcode)], limit=1)

        if not product_id:
            scanned_barcode = self.barcode
            self.barcode = False
            return {
                'warning': {
                    'title': self.env._('Warning!'),
                    'message': self.env._('No product is available for barcode "%s"', scanned_barcode)
                }
            }

        match = False
        if self.move_ids:
            for line in self.move_ids:
                if line.product_id == product_id:
                    line.quantity += 1
                    match = True
                    break

        if not match:
            new_move = self.env['stock.move'].new({
                'picking_id': self.id,
                'product_id': product_id.id,
                'uom_id': product_id.uom_id.id,
                'product_uom_qty': 1.0,
                'quantity': 1.0,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'barcode': product_id.barcode,
            })
            self.move_ids += new_move

        # Reset barcode field so subsequent scans of the same barcode trigger onchange
        self.barcode = False

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class StockMoveLine(models.Model):
    """
    StockMoveLine class is used to assigning serial number to the received products
    """
    _inherit = 'stock.move.line'

    lot_serial_name = fields.Char(string='Scanned Lot Serial',
                                  help="Stores the lot or serial number captured through barcode scanning.")
    is_barcode_scanned = fields.Boolean(string='Barcode Scanned',
                                        help="Indicates whether the record was created or updated using barcode scanning.")
    had_location_by_barcode = fields.Boolean(
        string='Had Location By Barcode',
        help="Indicates whether the source location was assigned by barcode scanning.")
    had_location_by_barcode_dest = fields.Boolean(
        string='Had Location By Barcode Destination',
        help="Indicates whether the destination location was assigned by barcode scanning.")

    def batch_read(self, fields_list):
        """Read records and include product quantity from related move."""
        response = self.read(fields_list)
        for rec in self:
            matching_obj = next(
                (obj for obj in response if obj.get('id') == rec.id), None)
            if matching_obj:
                matching_obj['move_id'] = rec.move_id.read(["product_uom_qty"])
        return response

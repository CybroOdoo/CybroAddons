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


class StockPicking(models.Model):
    """
    Model extending stock.picking.batch to support barcode scanning operations and tracking scanned products in batch transfers.
    """
    _inherit = 'stock.picking.batch'

    barcode_recent_scan = fields.Char(string='Recent Scan',
                                      help="Stores the latest scanned barcode value.")
    last_scan_tracking = fields.Char(string='Last Scan Tracking',
                                     help="Stores the tracking or serial information from the last scan.")
    last_scanned_product = fields.Many2one('product.product', string='Last Scanned Product',
                                           help="Represents the product identified from the most recent barcode scan.")

    def batch_barcode_move_line_fields(self):
        """Return the fields required for batch barcode move lines."""
        return ["product_id", "quantity_product_uom", "location_id", "location_dest_id", "picking_id",
                "quantity_product_uom", "tracking", "move_id", "result_package_id", "lot_id", "is_barcode_scanned"]

    def get_barcode_batch_move_line(self):
        """Return barcode-related move line data for the batch."""
        self.ensure_one()
        response = self.move_line_ids.sorted(key=lambda l: l.write_date).batch_read(self.batch_barcode_move_line_fields())
        return response

    def get_barcode_batch_fields(self):
        """Return the fields required for batch barcode operations."""
        return ["name", "picking_type_id", "state", "barcode_recent_scan", "last_scan_tracking", "last_scanned_product"]

    def get_barcode_batch(self):
        """Read and return barcode-related batch data."""
        self.ensure_one()
        response = self.read(self.get_barcode_batch_fields())
        response[0]['picking_type'] = self.picking_type_id.code
        return response

    def open_batch_record(self):
        """Open the custom batch barcode client action."""
        return {
            "type": "ir.actions.client",
            "name": self.name,
            "tag": "custom_batch_lines_client_action",
            "target": "current",
            'params': {'id': self.id,
                       'name': self.name},
        }

    def open_batch_picking(self):
        """Open the current batch picking record in form view."""
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.batch',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

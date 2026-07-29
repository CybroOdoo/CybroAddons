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
    Model extending stock.picking to support barcode scanning operations and tracking scanned products.
    """
    _inherit = 'stock.picking'

    with_barcode = fields.Boolean(string='With Barcode',
                                  help="Indicates whether barcode scanning is enabled for this operation.")
    barcode_recent_scan = fields.Char(string='Recent Scan',
                                      help="Stores the most recently scanned barcode value.")
    last_scan_tracking = fields.Char(string='Last Scan Tracking',
                                     help="Stores the tracking number or code from the last scan.")
    last_scanned_product = fields.Many2one('product.product', string='Last Scanned Product',
                                           help="References the product identified in the most recent barcode scan.")

    def open_record(self):
        """Open the custom stock picking client action for this record."""
        return {
            "type": "ir.actions.client",
            "name": self.name,
            "tag": "custom_location_client_action",
            "target": "current",
            "context": {
                'menu': 'custom_stock_picking_client_action',
            },
            'params': {'id': self.id,
                       'name': self.name},
        }

    def open_picking(self):
        """Open the current stock picking record in form view."""
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def picking_barcode_fields(self):
        """Return the fields required for barcode picking operations."""
        return ["name", "location_id", "location_dest_id", "state", "barcode_recent_scan", "last_scan_tracking",
                "last_scanned_product", "with_barcode", "picking_type_id"]

    def get_barcode_picking(self):
        """Read and return barcode-related picking data."""
        self.ensure_one()
        response = self.read(self.picking_barcode_fields())
        for res in response:
            res['picking_type'] = self.picking_type_id.code
        return response

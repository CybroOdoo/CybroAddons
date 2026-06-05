# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok(odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """
    Inherits Purchase Order Line to add extra fields and functionalities related
    to the creation of the automatic stock lot creation.
    """
    _inherit = "purchase.order.line"

    lot_id = fields.Many2one('custom.stock.lot',string='Lot',
                             domain="[('id', '=', 0)]",
                             help="Lot name to create for this order line")
    is_lot_product = fields.Boolean(string="Lot Product",
        help="Indicates whether the product is tracked by lot/serial number.")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id.tracking == 'lot':
            self.is_lot_product=True
        else:
            self.is_lot_product = False

    def _create_stock_moves(self, picking):
        """Override to create stock.move.line with lot info after creating stock.move."""
        all_moves = self.env['stock.move']
        for line in self:
            move = super(PurchaseOrderLine, line)._create_stock_moves(picking)
            line_move_line_vals = {
                'company_id': line.env.company.id,
                'picking_id': move.picking_id.id,
                'product_id': line.product_id.id,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
                'lot_name': line.lot_id.name if line.lot_id else False,
                'quantity': line.product_uom_qty,
                'description_picking': line.product_id.display_name,
                'move_id': move.id
            }
            self.env['stock.move.line'].create(line_move_line_vals)
            all_moves |= move
        return all_moves

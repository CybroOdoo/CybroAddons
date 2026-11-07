# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
"""Stock move extension for multiple delivery addresses."""
from odoo import models


class StockMove(models.Model):
    """ Inherits stock_move to manage pickings with respect to the
        delivery address """

    # pylint: disable=protected-access,too-few-public-methods
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        """ Extending _get_new_picking_values to create values for new
         pickings with different delivery addresses"""
        res = super()._get_new_picking_values()
        partner_id = (
            self.sale_line_id.delivery_addr_id[:1].id
            or self.sale_line_id.order_id.partner_shipping_id[:1].id
            or self.sale_line_id.order_id.partner_id[:1].id
        )
        if partner_id:
            res['partner_id'] = partner_id
        return res

    def _assign_picking(self):
        """Create separate deliveries per address, ensuring all products are included."""
        sale_moves = self.filtered(lambda m: m.sale_line_id)
        other_moves = self - sale_moves
        if other_moves:
            super(StockMove, other_moves)._assign_picking()

        if not sale_moves:
            return True

        picking_obj = self.env['stock.picking']
        moves_by_address = {}
        for move in sale_moves:
            partner_id = (
                move.sale_line_id.delivery_addr_id.id
                or move.sale_line_id.order_id.partner_shipping_id.id
                or move.sale_line_id.order_id.partner_id.id
            )

            if partner_id not in moves_by_address:
                moves_by_address[partner_id] = self.env['stock.move']
            moves_by_address[partner_id] += move

        for partner_id, moves in moves_by_address.items():
            moves = moves.filtered(lambda m: m.uom_id.compare(m.product_uom_qty, 0.0) >= 0)
            if not moves:
                continue

            picking_vals = moves._get_new_picking_values()
            if partner_id:
                picking_vals['partner_id'] = partner_id
            picking = picking_obj.create(picking_vals)
            moves.write({'picking_id': picking.id})
            moves._assign_picking_post_process(new=True)

        return True

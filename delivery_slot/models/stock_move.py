# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Muhsina V (odoo@cybrosys.com)
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
from odoo import models
from odoo.tools import float_compare
from odoo.tools.misc import groupby
from odoo.addons.stock.models.stock_move import StockMove


class StockMoves(models.Model):
    """Inheriting the stock move model"""
    _inherit = 'stock.move'

    def _assign_picking(self):
        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations, and picking
        type (moves should already have them identical). Otherwise, create a
        new picking to assign them to. """
        picking_obj = self.env['stock.picking']
        grouped_moves = groupby(self,
                                key=lambda m: m._key_assign_picking())
        for group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*moves)
            # Could pass the arguments contained in group, but they are the
            # same for each move that's why moves[0] is acceptable
            picking = moves[0]._search_picking_for_assignation()
            if picking:
                # If a picking is found, we'll append `move` to its move list
                # and thus its `partner_id` and `ref` field will refer to
                # multiple records.
                # In this case, we chose to wipe them.
                vals = {}
                if any(picking.partner_id.id != m.partner_id.id for m in
                       moves):
                    vals['partner_id'] = False
                if any(picking.origin != m.origin for m in moves):
                    vals['origin'] = False
                if vals:
                    picking.write(vals)
            else:
                # Don't create picking for negative moves since they will be
                # reversed and assigned to another picking
                moves = moves.filtered(lambda m: float_compare(
                    m.product_uom_qty, 0.0, precision_rounding=
                    m.product_uom.rounding) >= 0)
                if not moves:
                    continue
                pick_values = moves._get_new_picking_values()
                sale_order = self.env['sale.order'].search([
                    ('name', '=', pick_values['origin'])])
                if sale_order.slot_per_product:
                    for move in moves:
                        new_picking = picking_obj.create(
                            move._get_new_picking_values())
                        move.write({'picking_id': new_picking.id})
                        move._assign_picking_post_process(new=new_picking)
                else:
                    new_picking = picking_obj.create(
                        moves._get_new_picking_values())
                    moves.write({'picking_id': new_picking.id})
                    moves._assign_picking_post_process(new=new_picking)
        return True
    StockMove._assign_picking = _assign_picking

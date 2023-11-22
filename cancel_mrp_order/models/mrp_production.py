# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from collections import defaultdict
from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools import float_round


class MrpProduction(models.Model):
    """Inherit manufacturing order to add some function """
    _inherit = 'mrp.production'

    def checking_access(self, rec):
        """Warning for cancel button in action"""
        if self.state == 'done':
            rec.action_cancel_manufacturing_order()
        else:
            raise UserError(_(
                "You cannot cancel an order that is not in Done state!"))

    def _create_move_from_existing_move(self, move, factor, location_id,
                                        location_dest_id):
        """Create a stock move while creating a manufacturing order"""
        return self.env['stock.move'].create({
            'name': move.name,
            'date': move.create_date,
            'product_id': move.product_id.id,
            'product_uom_qty': move.product_uom_qty * factor,
            'product_uom': move.product_uom.id,
            'procure_method': 'make_to_stock',
            'location_dest_id': location_dest_id.id,
            'location_id': location_id.id,
            'warehouse_id': location_dest_id.warehouse_id.id,
            'company_id': move.company_id.id,
        })

    def action_cancel_manufacturing_order(self):
        """To cancel manufacturing order while clicking the button cancel """
        consume_moves = self.env['stock.move']
        produce_moves = self.env['stock.move']
        factor = self.product_qty / self.product_uom_id._compute_quantity(
            self.product_qty, self.product_uom_id)
        finished_moves = self.move_finished_ids.filtered(
            lambda l: l.state == 'done')
        raw_moves = self.move_raw_ids.filtered(
            lambda l: l.state == 'done')
        for finished_move in finished_moves:
            consume_moves += self._create_move_from_existing_move(
                finished_move, factor, finished_move.location_dest_id,
                finished_move.location_id)
        for raw_move in raw_moves:
            produce_moves += self._create_move_from_existing_move(
                raw_move, factor, raw_move.location_dest_id,
                self.location_dest_id)
        if consume_moves:
            consume_moves._action_confirm()
        if produce_moves:
            produce_moves._action_confirm()
        finished_moves = consume_moves.filtered(
            lambda m: m.product_id == self.product_id)
        consume_moves -= finished_moves
        for finished_move in finished_moves:
            if finished_move.has_tracking != 'none':
                self.env['stock.move.line'].create({
                    'move_id': finished_move.id,
                    'qty_done': finished_move.product_uom_qty,
                    'product_id': finished_move.product_id.id,
                    'product_uom_id': finished_move.product_uom.id,
                    'location_id': finished_move.location_id.id,
                    'location_dest_id': finished_move.location_dest_id.id,
                })
            else:
                finished_move.quantity_done = finished_move.product_uom_qty
        qty_already_used = defaultdict(float)
        for move in produce_moves | consume_moves:
            if move.has_tracking != 'none':
                original_move = move in produce_moves and self.move_raw_ids or\
                                self.move_finished_ids
                moves_lines = original_move.filtered(
                    lambda m: m.product_id == move.product_id).mapped(
                    'move_line_ids')
                for move_line in moves_lines:
                    taken_quantity = min(move.product_uom_qty,
                                         move_line.qty_done - qty_already_used[
                                             move_line])
                    if taken_quantity:
                        self.env['stock.move.line'].create({
                            'move_id': move.id,
                            'lot_id': move_line.lot_id.id,
                            'qty_done': taken_quantity,
                            'product_id': move.product_id.id,
                            'product_uom_id': move_line.product_uom_id.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                        })
                        move.product_uom_qty -= taken_quantity
                        qty_already_used[move_line] += taken_quantity
            else:
                move.quantity_done = float_round(
                    move.product_uom_qty,
                    precision_rounding=move.product_uom.rounding)
        finished_moves._action_done()
        consume_moves._action_done()
        produce_moves._action_done()
        produced_move_line_ids = produce_moves.mapped(
            'move_line_ids').filtered(lambda ml: ml.qty_done > 0)
        consume_moves.mapped('move_line_ids').write(
            {'produce_line_ids': [(6, 0, produced_move_line_ids.ids)]})
        raw_moves.sudo().write(
            {'state': 'cancel',
             })
        raw_moves.mapped(
            'move_line_ids').sudo().write({'state': 'cancel'})
        if self.sudo().mapped('workorder_ids'):
            self.sudo().mapped('workorder_ids').write({'state': 'cancel'})
        self.write({'state': 'cancel'})

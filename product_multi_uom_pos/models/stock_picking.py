# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: LINTO C T(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models
from itertools import groupby


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        return {
            'name': first_line.name,
            'product_uom': first_line.uom_id.id,
            'picking_id': self.id,
            'picking_type_id': self.picking_type_id.id,
            'product_id': first_line.product_id.id,
            'product_uom_qty': abs(sum(order_lines.mapped('qty'))),
            'state': 'draft',
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'company_id': self.company_id.id,
   }

    def _create_move_from_pos_order_lines(self, lines):
        self.ensure_one()
        lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id),
                                   key=lambda l: (l.product_id.id, l.uom_id.id))
        for product, lines in lines_by_product:
            order_lines = self.env['pos.order.line'].concat(*lines)
            first_line = order_lines[0]
            current_move = self.env['stock.move'].create(
                self._prepare_stock_move_vals(first_line, order_lines)
            )
            confirmed_moves = current_move._action_confirm()
            for move in confirmed_moves:
                if first_line.product_id == move.product_id and first_line.product_id.tracking != 'none':
                    if self.picking_type_id.use_existing_lots or self.picking_type_id.use_create_lots:
                        for line in order_lines:
                            sum_of_lots = 0
                            for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
                                if line.product_id.tracking == 'serial':
                                    qty = 1
                                else:
                                    qty = abs(line.qty)
                                ml_vals = move._prepare_move_line_vals()
                                ml_vals.update({'qty_done': qty})
                                if self.picking_type_id.use_existing_lots:
                                    existing_lot = self.env['stock.production.lot'].search([
                                        ('company_id', '=', self.company_id.id),
                                        ('product_id', '=', line.product_id.id),
                                        ('name', '=', lot.lot_name)
                                    ])
                                    if not existing_lot and self.picking_type_id.use_create_lots:
                                        existing_lot = self.env['stock.production.lot'].create({
                                            'company_id': self.company_id.id,
                                            'product_id': line.product_id.id,
                                            'name': lot.lot_name,
                                        })
                                    ml_vals.update({
                                        'lot_id': existing_lot.id,
                                    })
                                else:
                                    ml_vals.update({
                                        'lot_name': lot.lot_name,
                                    })
                                self.env['stock.move.line'].create(ml_vals)
                                sum_of_lots += qty
                            if abs(line.qty) != sum_of_lots:
                                difference_qty = abs(line.qty) - sum_of_lots
                                ml_vals = current_move._prepare_move_line_vals()
                                if line.product_id.tracking == 'serial':
                                    ml_vals.update({'qty_done': 1})
                                    for i in range(int(difference_qty)):
                                        self.env['stock.move.line'].create(ml_vals)
                                else:
                                    ml_vals.update({'qty_done': difference_qty})
                                    self.env['stock.move.line'].create(ml_vals)
                    else:
                        move._action_assign()
                        sum_of_lots = 0
                        for move_line in move.move_line_ids:
                            move_line.qty_done = move_line.product_uom_qty
                            sum_of_lots += move_line.product_uom_qty
                        if float_compare(move.product_uom_qty, move.quantity_done,
                                         precision_rounding=move.product_uom.rounding) > 0:
                            remaining_qty = move.product_uom_qty - move.quantity_done
                            ml_vals = move._prepare_move_line_vals()
                            ml_vals.update({'qty_done': remaining_qty})
                            self.env['stock.move.line'].create(ml_vals)
                else:
                    move.quantity_done = move.product_uom_qty

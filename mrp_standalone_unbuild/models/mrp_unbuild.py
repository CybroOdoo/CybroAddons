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

from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare

class MrpUnbuild(models.Model):
    """Adding the component lines and removing the required attribute of MO fields"""
    _inherit = 'mrp.unbuild'

    mo_id = fields.Many2one(
        'mrp.production', 
        'Manufacturing Order', required=False,
        help="Custom unrequired Manufacturing Order connection"
    )
    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material',
        readonly=False, required=False, states={'done': [('readonly', True)]}, check_company=True,
        help="Bill of Materials to be used to unbuild the product"
    )
    unbuild_line_ids = fields.One2many('mrp.unbuild.line', 'unbuild_id', string='Unbuild Lines',
                                       help='Unbuild lines from the BOM or Manually added')

    @api.onchange('bom_id', 'product_qty')
    def _onchange_bom_id_populate_lines(self):
        """auto update of component lines based on bom"""
        if self.bom_id:
            lines = []
            # Calculate factor based on BoM quantity
            factor = self.product_uom_id._compute_quantity(self.product_qty, self.bom_id.product_uom_id) / self.bom_id.product_qty
            # Use explode to get all components correctly
            boms, bom_lines = self.bom_id.explode(self.product_id, factor, picking_type=self.bom_id.picking_type_id)
            for line, line_data in bom_lines:
                lines.append(Command.create( {
                    'product_id': line.product_id.id,
                    'qty': line_data['qty'],
                    'uom_id': line.product_uom_id.id or line.product_id.uom_id.id,
                    'bom_line_id': line.id,
                }))
            # Also handle byproducts
            for byproduct in self.bom_id.byproduct_ids:
                if byproduct._skip_byproduct_line(self.product_id):
                    continue
                quantity = byproduct.product_qty * factor
                lines.append(Command.create({
                    'product_id': byproduct.product_id.id,
                    'qty': quantity,
                    'uom_id': byproduct.product_uom_id.id or byproduct.product_id.uom_id.id,
                    'byproduct_id': byproduct.id,
                }))
            self.unbuild_line_ids = [Command.clear()] + lines
        else:
            self.unbuild_line_ids = [Command.clear()]

    def action_unbuild(self):
        """follow Odoo default if there is Manufacturing order selected and vice-versa if there is no"""
        self.ensure_one()
        if self.mo_id:
            return super().action_unbuild()
        self._check_company()
        if self.product_id.tracking != 'none' and not self.lot_id.id:
            raise ValidationError(_('You should provide a lot number for the final product.'))
        consume_moves = self._generate_consume_moves()
        produce_moves = self._generate_produce_moves()
        if self.bom_id.picking_type_id:
            (consume_moves | produce_moves).write({'picking_type_id': self.bom_id.picking_type_id.id})
        consume_moves._action_confirm()
        produce_moves._action_confirm()
        finished_moves = consume_moves.filtered(lambda m: m.product_id == self.product_id)
        result_moves = (consume_moves - finished_moves) | produce_moves
        all_moves = finished_moves | result_moves
        for move in all_moves:
            move.quantity = move.product_uom_qty
            move.picked = True
            if not move.unbuild_id:
                move.unbuild_id = self.id
            if not move.move_line_ids:
                if move in finished_moves:
                    self._prepare_finished_move_line_vals(move)
                else:
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'quantity': move.product_uom_qty,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'company_id': self.company_id.id,
                        'picked': True,
                    })
            else:
                move.move_line_ids.write({'picked': True})
                total_line_qty = sum(move.move_line_ids.mapped('quantity'))
                if float_compare(total_line_qty, move.quantity, precision_rounding=move.product_uom.rounding) != 0:
                    last_line = move.move_line_ids[-1]
                    last_line.quantity += (move.quantity - total_line_qty)
        finished_moves._action_done()
        self.env.flush_all()
        total_value = 0
        if hasattr(finished_moves, 'stock_valuation_layer_ids'):
            total_value = -sum(finished_moves.stock_valuation_layer_ids.mapped('value'))
        in_moves = result_moves.filtered(lambda m: m._is_in())
        if total_value > 0 and in_moves:
            weights = []
            total_weight = 0
            for move in in_moves:
                qty_in_default_uom = move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
                weight = move.product_id.standard_price * qty_in_default_uom
                weights.append(weight)
                total_weight += weight
            if total_weight <= 0:
                total_weight = sum(in_moves.mapped('quantity'))
                weights = list(in_moves.mapped('quantity'))
            if total_weight > 0:
                for i, move in enumerate(in_moves):
                    if move.quantity > 0:
                        move.price_unit = (total_value * (weights[i] / total_weight)) / move.quantity
        result_moves._action_done()
        produced_move_line_ids = in_moves.mapped('move_line_ids').filtered(lambda ml: ml.quantity > 0)
        finished_moves.mapped('move_line_ids').write({'produce_line_ids': [(6, 0, produced_move_line_ids.ids)]})
        return self.write({'state': 'done'})

    def _generate_consume_moves(self):
        """ Override to avoid duplicate byproducts when using custom lines. """
        if not self.mo_id and self.unbuild_line_ids:
            return self._generate_move_from_bom_line(self.product_id, self.product_uom_id, self.product_qty)
        return super()._generate_consume_moves()

    def _generate_produce_moves(self):
        """ Override to use custom unbuild_line_ids if present. """
        if not self.mo_id and self.unbuild_line_ids:
            moves = self.env['stock.move']
            for line in self.unbuild_line_ids:
                product_prod_location = line.product_id.with_company(self.company_id).property_stock_production
                move_vals = {
                    'name': self.name,
                    'date': self.create_date,
                    'bom_line_id': line.bom_line_id.id,
                    'byproduct_id': line.byproduct_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': (line.uom_id.id or line.product_id.uom_id.id),
                    'location_id': product_prod_location.id,
                    'location_dest_id': self.location_dest_id.id,
                    'warehouse_id': self.location_dest_id.warehouse_id.id,
                    'procure_method': 'make_to_stock',
                    'unbuild_id': self.id,
                    'company_id': self.company_id.id,
                }
                if line.lot_id:
                    move_vals['move_line_ids'] = [Command.create({
                        'product_id': line.product_id.id,
                        'lot_id': line.lot_id.id,
                        'quantity': line.qty,
                        'product_uom_id': line.uom_id.id or line.product_id.uom_id.id,
                        'location_id': product_prod_location.id,
                        'location_dest_id': self.location_dest_id.id,
                        'company_id': self.company_id.id,
                    })]
                moves += self.env['stock.move'].create(move_vals)
            return moves
        return super()._generate_produce_moves()

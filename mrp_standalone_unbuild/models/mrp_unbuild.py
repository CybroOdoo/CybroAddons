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


class MrpUnbuild(models.Model):
    """Setting Unbuild order without the need of Manufacturing Order"""
    _inherit = 'mrp.unbuild'

    mo_id = fields.Many2one(
        'mrp.production',
        'Manufacturing Order', required=False,
        help="Custom unrequired Manufacturing Order connection"
    )
    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material',
        readonly=False, required=False,
        states={'done': [('readonly', True)]}, check_company=True,
        help="Bill of Materials to be used to unbuild the product"
    )
    allowed_lot_ids = fields.Many2many(
        'stock.lot',
        string='Allowed Lots',
        compute='_compute_allowed_lot_ids',
        help='Allowed lots especially in case if there is no MO selected'
    )
    unbuild_line_ids = fields.One2many('mrp.unbuild.line', 'unbuild_id', string='Unbuild Lines',
                                       help='Unbuild lines from the BOM or Manually added')

    @api.depends('mo_id', 'product_id', 'company_id')
    def _compute_allowed_lot_ids(self):
        for rec in self:
            if rec.mo_id:
                rec.allowed_lot_ids = rec.mo_id.lot_producing_ids
            elif rec.product_id:
                rec.allowed_lot_ids = self.env['stock.lot'].search([
                    ('product_id', '=', rec.product_id.id),
                    '|', ('company_id', '=', rec.company_id.id), ('company_id', '=', False)
                ])
            else:
                rec.allowed_lot_ids = self.env['stock.lot']

    @api.onchange('bom_id', 'product_qty')
    def _onchange_bom_id_populate_lines(self):
        """adding component lines to unbuild the product from BOM if any"""
        if self.bom_id:
            lines = []
            # Calculate factor based on BoM quantity
            factor = self.product_uom_id._compute_quantity(self.product_qty,
                                                           self.bom_id.product_uom_id) / self.bom_id.product_qty
            # Use explode to get all components correctly
            boms, bom_lines = self.bom_id.explode(self.product_id, factor, picking_type=self.bom_id.picking_type_id)
            for line, line_data in bom_lines:
                lines.append(Command.create({
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
        """Unbuilding the selected product and components"""
        self.ensure_one()
        if self.mo_id:
            return super().action_unbuild()
        # Logic for unbuild WITHOUT MO
        self._check_company()
        if self.product_id.tracking != 'none' and not self.lot_id.id:
            raise ValidationError(_('You should provide a lot number for the final product.'))
        consume_moves = self._generate_consume_moves()
        consume_moves._action_confirm()
        produce_moves = self._generate_produce_moves()
        produce_moves._action_confirm()
        finished_moves = consume_moves.filtered(lambda m: m.product_id == self.product_id)
        consume_moves -= finished_moves
        # Ensure byproducts and components have their quantities and move lines set
        for move in (consume_moves | produce_moves):
            if move.product_uom.compare(move.product_uom_qty, move.quantity) > 0:
                move_line_vals = {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': move.product_uom_qty - move.quantity,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'company_id': self.company_id.id,
                }
                self.env['stock.move.line'].create(move_line_vals)
                move.quantity = move.product_uom_qty
        # We skip the check that raises "Please specify a manufacturing order"
        # because the user is providing the component lots/lines manually.
        for finished_move in finished_moves:
            if finished_move.product_uom.compare(finished_move.product_uom_qty, finished_move.quantity) > 0:
                finished_move_line_vals = self._prepare_finished_move_line_vals(finished_move)
                self.env['stock.move.line'].create(finished_move_line_vals)
        # Skip the complex lot matching logic that requires self.mo_id
        # The produce_moves already have their move_line_ids if lot_id was set in the custom lines.
        (finished_moves | consume_moves | produce_moves).picked = True
        finished_moves._action_done()
        consume_moves._action_done()
        produce_moves._action_done()
        # Link consume lines to produce lines if possible (standard Odoo does this)
        produced_move_line_ids = produce_moves.mapped('move_line_ids').filtered(lambda ml: ml.quantity > 0)
        consume_moves.mapped('move_line_ids').write({
            'produce_line_ids': [Command.set(produced_move_line_ids.ids)]
        })
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
                if line.qty:
                    product_prod_location = line.product_id.with_company(self.company_id).property_stock_production
                    move_vals = {
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

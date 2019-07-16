# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import math


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

    mrp_sec_qty = fields.Float(string='Product Secondary Qty')
    mrp_sec_uom = fields.Many2one('product.uom', string='Secondary Unit')

    @api.model
    def default_get(self, fields):
        res = super(ChangeProductionQty, self).default_get(fields)
        prod_obj = self.env['mrp.production']
        prod = prod_obj.browse(self._context.get('active_id'))
        if 'product_qty' in fields:
            res.update({'product_qty': prod.product_qty})
        if 'mrp_sec_qty' in fields:
            res.update({'mrp_sec_qty': prod.mrp_sec_qty})
        if 'mrp_sec_uom' in fields:
            res.update({'mrp_sec_uom': prod.mrp_sec_uom.id})
        return res

    @api.model
    def _update_product_to_produce(self, production, qty, ratio, sec_uom):
        production_move = production.move_finished_ids.filtered(lambda x:x.product_id.id == production.product_id.id and x.state not in ('done', 'cancel'))

        if production_move:
            production_move.write({
                'product_uom_qty': qty,
                'stock_move_sec_uom': sec_uom.id,
                'ratio_sec_uom': ratio,
                                   })
        else:
            production_move = production._generate_finished_moves()
            production_move = production.move_finished_ids.filtered(lambda x : x.state not in ('done', 'cancel') and production.product_id.id == x.product_id.id)
            production_move.write({
                'product_uom_qty': qty,
                'stock_move_sec_uom': sec_uom.id,
                'ratio_sec_uom': ratio,
                                   })

    @api.multi
    def change_prod_qty(self):
        for wizard in self:
            production = wizard.mo_id
            produced = sum(production.move_finished_ids.mapped('quantity_done'))
            if wizard.product_qty < produced:
                raise UserError(_("You have already processed %d. Please input a quantity higher than %d ")%(produced, produced))
            ratio = wizard.mrp_sec_qty/wizard.product_qty
            production.write({'product_qty': wizard.product_qty,
                              'mrp_sec_qty':  wizard.mrp_sec_qty,
                              'mrp_sec_uom': wizard.mrp_sec_uom.id,
                              'mrp_ratio_sec_uom': ratio
                              })
            factor = production.product_uom_id._compute_quantity(production.product_qty - production.qty_produced, production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.product_id, factor, picking_type=production.bom_id.picking_type_id)
            for line, line_data in lines:
                production._update_raw_move(line, line_data)
            operation_bom_qty = {}
            for bom, bom_data in boms:
                for operation in bom.routing_id.operation_ids:
                    operation_bom_qty[operation.id] = bom_data['qty']

            self._update_product_to_produce(production, production.product_qty - production.qty_produced,
                                            ratio, production.mrp_sec_uom)
            moves = production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            moves.do_unreserve()
            moves.action_assign()
            for wo in production.workorder_ids:
                operation = wo.operation_id
                if operation_bom_qty.get(operation.id):
                    cycle_number = math.ceil(operation_bom_qty[operation.id] / operation.workcenter_id.capacity)  # TODO: float_round UP
                    wo.duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
                if production.product_id.tracking == 'serial':
                    quantity = 1.0
                else:
                    quantity = wo.qty_production - wo.qty_produced
                    quantity = quantity if (quantity > 0) else 0
                wo.qty_producing = quantity
                if wo.qty_produced < wo.qty_production and wo.state == 'done':
                    wo.state = 'progress'
                # assign moves; last operation receive all unassigned moves
                # TODO: following could be put in a function as it is similar as code in _workorders_create
                # TODO: only needed when creating new moves
                moves_raw = production.move_raw_ids.filtered(lambda move: move.operation_id == operation and move.state not in ('done', 'cancel'))
                if wo == production.workorder_ids[-1]:
                    moves_raw |= production.move_raw_ids.filtered(lambda move: not move.operation_id)
                moves_finished = production.move_finished_ids.filtered(lambda move: move.operation_id == operation) #TODO: code does nothing, unless maybe by_products?
                moves_raw.mapped('move_lot_ids').write({'workorder_id': wo.id})
                (moves_finished + moves_raw).write({'workorder_id': wo.id})
                if wo.move_raw_ids.filtered(lambda x: x.product_id.tracking != 'none') and not wo.active_move_lot_ids:
                    wo._generate_lot_ids()
        return {}

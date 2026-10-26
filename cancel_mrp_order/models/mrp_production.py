# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import Command, models
from odoo.exceptions import AccessError, UserError

CANCEL_GROUP = (
    'cancel_mrp_order.cancel_mrp_order_group_cancel_manufacturing_order')


class MrpProduction(models.Model):
    """Extend the manufacturing order to allow cancelling a done order."""
    _inherit = 'mrp.production'

    def action_cancel_manufacturing_order(self):
        """Cancel done manufacturing orders and reverse their stock."""
        if not self.env.user.has_group(CANCEL_GROUP):
            raise AccessError(self.env._(
                "You are not allowed to cancel manufacturing orders."))
        for order in self:
            if order.state != 'done':
                raise UserError(self.env._(
                    "You cannot cancel an order that is not in the Done "
                    "state."))
            done_moves = (
                order.move_finished_ids | order.move_raw_ids
            ).filtered(lambda move: move.state == 'done')
            order._reverse_done_moves(done_moves)
            order.workorder_ids.write({'state': 'cancel'})
            order.write({'state': 'cancel'})

    def _reverse_done_moves(self, moves):
        """Reverse the done quantity of each move with a stock move."""
        reverse_moves = self.env['stock.move']
        for move in moves:
            reverse_moves |= self.env['stock.move'].create({
                'origin': self.name,
                'product_id': move.product_id.id,
                'uom_id': move.uom_id.id,
                'product_uom_qty': move.quantity,
                'location_id': move.location_dest_id.id,
                'location_dest_id': move.location_id.id,
                'company_id': move.company_id.id,
                'picked': True,
                'move_line_ids': [Command.create({
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'location_id': line.location_dest_id.id,
                    'location_dest_id': line.location_id.id,
                    'lot_id': line.lot_id.id,
                    'quantity': line.quantity,
                    'picked': True,
                }) for line in move.move_line_ids],
            })
        reverse_moves._action_done()

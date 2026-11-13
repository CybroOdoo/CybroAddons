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
from odoo import api, fields, models


class StockPicking(models.Model):
    """Inherit stock.picking to provide automated done quantity filling
    and line selection."""
    _inherit = 'stock.picking'

    select_all_toggle = fields.Boolean(
        string="All",
        compute='_compute_select_all_toggle',
        help="Technical field indicating if all move lines are selected",
        copy=False,
    )

    @api.depends('move_ids.product_select')
    def _compute_select_all_toggle(self):
        """Compute whether all move lines are selected."""
        for picking in self:
            picking.select_all_toggle = bool(picking.move_ids) and all(
                move.product_select for move in picking.move_ids
            )

    def action_select_all(self):
        """Select all product lines in the transfer."""
        for picking in self:
            picking.move_ids.write({'product_select': True})

    def action_unselect_all(self):
        """Unselect all product lines in the transfer."""
        for picking in self:
            picking.move_ids.write({'product_select': False})

    def action_fill_done_qty(self):
        """Set the done quantity for selected stock moves based on availability."""
        for picking in self:
            for move in picking.move_ids.filtered(lambda m: m.product_select):
                if move.picking_code == 'incoming':
                    move.write({'quantity': move.product_uom_qty})
                elif move.forecast_availability > 0:
                    move.write({
                        'quantity': min(move.product_uom_qty, move.forecast_availability)
                    })

    def action_unfill_done_qty(self):
        """Reset the done quantity to 0 for selected stock moves."""
        for picking in self:
            selected_moves = picking.move_ids.filtered(lambda m: m.product_select)
            selected_moves.write({'quantity': 0.0})

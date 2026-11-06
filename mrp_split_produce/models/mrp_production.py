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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################
from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """Inherits the mrp.production model to support partial production
    and manual finalization of manufacturing orders."""
    _inherit = 'mrp.production'

    is_partially_produced = fields.Boolean(
        string='Partially Produced',
        default=False,
        copy=False,
        help="Indicates whether the manufacturing order is partially produced",
    )
    is_finalized = fields.Boolean(
        string='MO Finalized',
        default=False,
        copy=False,
        help="Is MO Finalized",
    )

    @api.depends('is_partially_produced')
    def _compute_state(self):
        """Compute the manufacturing order state based on partial production."""
        super()._compute_state()
        for production in self:
            if production.state in ('done', 'cancel'):
                continue
            if production.is_partially_produced:
                production.state = 'progress'

    def action_produce_all_custom(self):
        """Perform production (component consumption) without
        marking the MO as done."""
        self.ensure_one()
        if self.state in ('done', 'cancel'):
            raise UserError(
                _("Cannot produce a closed or cancelled manufacturing order."),
            )
        if self.is_partially_produced:
            raise UserError(
                _("This manufacturing order is already partially produced."),
            )

        self.workorder_ids.button_finish()

        raw_moves = self.move_raw_ids.filtered(
            lambda m: m.state not in ('done', 'cancel'),
        )
        for move in raw_moves:
            if move.quantity == 0 and move.product_uom_qty > 0:
                move.quantity = move.product_uom_qty
        if raw_moves:
            raw_moves.picked = True
            raw_moves.move_line_ids.picked = True
            raw_moves._action_done()

        self.write({
            'is_partially_produced': True,
        })
        return True

    def action_finalize_mo(self):
        """Finalize the manufacturing order using the standard button_mark_done
        and _post_inventory flow, ensuring costing, lots, serials, and stock
        valuation are properly handled."""
        self.ensure_one()
        if not self.is_partially_produced:
            raise UserError(
                _("You must produce the order first by clicking 'Produce All'."),
            )
        res = self.button_mark_done()
        if self.state == 'done':
            self.is_finalized = True
        return res

    def button_mark_done(self):
        """Override to update is_finalized flag when production is marked done."""
        res = super().button_mark_done()
        for production in self:
            if production.state == 'done':
                production.is_finalized = True
        return res

    def _cal_price(self, consumed_moves):
        """Ensure consumed component moves are taken into account for costing
        when the MO is finalized after partial production."""
        for production in self:
            prod_consumed = consumed_moves
            if not prod_consumed and production.is_partially_produced:
                prod_consumed = production.move_raw_ids.filtered(
                    lambda m: m.state == 'done',
                )
            super(MrpProduction, production)._cal_price(prod_consumed)
        return True

    def _post_inventory(self, cancel_backorder=False):
        """Ensure consumed raw move lines are properly linked to finished
        move lines for traceability and valuation."""
        res = super()._post_inventory(cancel_backorder=cancel_backorder)
        for order in self:
            if order.is_partially_produced:
                done_raw_lines = order.move_raw_ids.filtered(
                    lambda m: m.state == 'done',
                ).move_line_ids
                if done_raw_lines:
                    finished_lines = order.move_finished_ids.filtered(
                        lambda m: m.product_id == order.product_id,
                    ).move_line_ids
                    for f_line in finished_lines:
                        missing = done_raw_lines - f_line.consume_line_ids
                        if missing:
                            f_line.consume_line_ids = [
                                Command.link(line.id) for line in missing
                            ]
        return res

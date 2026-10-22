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
from odoo import fields, models


class StockLandedCost(models.Model):
    """Inherits 'stock.landed.cost' model to add additional functionality
    related to cancelling and resetting landed cost records.

    Methods:
        action_landed_cost_cancel: Cancels the landed cost record by deleting
        its associated accounting entries and changes state
        to 'cancel'.

        action_landed_cost_reset_and_cancel: Resets the landed cost record by
        deleting its associated accounting entries.
        It changes the state back to 'draft'.

        action_landed_cost_cancel_and_delete: Deletes the landed cost record by
        deleting its associated accounting entries. It also
        deletes the Landed cost record.

        action_landed_cost_cancel_form: Cancels the landed cost record and
        deletes its associated accounting entries.
        It also creates two entries to revert back to the original cost price,
        which are also deleted in the process.

    """
    _inherit = 'stock.landed.cost'

    is_cancel = fields.Boolean(string='Cancel', default=False, copy=False,
                               help='If the user clicks the "Cancel" button '
                                    'once, it will hide the button and make '
                                    'it invisible.')

    def _revert_landed_cost(self):
        """Remove the journal entry and valuation adjustment lines, then let
        Odoo recompute the value of the affected stock moves (and with it the
        average cost of AVCO products)."""
        for rec in self:
            moves = rec.valuation_adjustment_lines.move_id
            was_done = rec.state == 'done'
            # Remove Journal Entry
            if rec.account_move_id:
                move = rec.account_move_id.sudo()
                if move.state == 'posted':
                    move.button_draft()
                move.unlink()
            # Remove valuation lines
            if rec.valuation_adjustment_lines:
                rec.valuation_adjustment_lines.sudo().unlink()
            # Landed costs are part of the move value only while the cost is
            # done, so the value (and the AVCO price) must be recomputed.
            if was_done and moves:
                moves.sudo()._set_value()

    # ---------------------------------------------------------
    # CANCEL
    # ---------------------------------------------------------
    def action_landed_cost_cancel(self):
        """Revert landed cost and set the record state to cancel."""
        for rec in self.filtered(lambda cost: cost.state in ('draft', 'done')):
            rec._revert_landed_cost()
            rec.write({'state': 'cancel', 'is_cancel': True})

    # ---------------------------------------------------------
    # RESET TO DRAFT
    # ---------------------------------------------------------
    def action_landed_cost_reset_and_cancel(self):
        """Revert landed cost and reset the record to draft."""
        for rec in self.filtered(lambda cost: cost.state != 'draft'):
            rec._revert_landed_cost()
            rec.write({'state': 'draft', 'is_cancel': False})

    # ---------------------------------------------------------
    # CANCEL AND DELETE
    # ---------------------------------------------------------
    def action_landed_cost_cancel_and_delete(self):
        """Revert landed cost, cancel the record, and delete it."""
        for rec in self:
            rec._revert_landed_cost()
            # Set state to 'cancel' first, then delete
            rec.write({'state': 'cancel', 'is_cancel': True})
            rec.unlink()

    # ---------------------------------------------------------
    # FORM BUTTON ACTION
    # ---------------------------------------------------------
    def action_landed_cost_cancel_form(self):
        """Handle form cancel action based on configured cancel mode."""
        records = self.filtered(lambda cost: cost.state == 'done')
        records._revert_landed_cost()
        landed_mode = self.env['ir.config_parameter'].sudo().get_str(
            'cancel_landed_cost_odoo.land_cost_cancel_modes', 'cancel'
        )

        # DELETE MODE
        if landed_mode == 'cancel_delete':
            for rec in records:
                rec.write({'state': 'cancel', 'is_cancel': True})
                rec.unlink()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {
                    'menu_id': self.env.ref(
                        'stock_landed_costs.menu_stock_landed_cost'
                    ).id
                }
            }

        # STATE MODE
        state = 'cancel' if landed_mode == 'cancel' else 'draft'
        records.write({'state': state, 'is_cancel': landed_mode == 'cancel'})

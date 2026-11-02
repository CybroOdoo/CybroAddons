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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""MRP Production model extension for Cancel MO."""
import logging
from odoo import api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    """Inheriting mrp.production to add cancel functionality in the done state."""
    _inherit = 'mrp.production'

    def _default_cancel_inventory(self):
        """Return default value from configuration settings."""
        return self.env['ir.config_parameter'].sudo().get_str(
            'cancel_mo.is_cancel_inventory_moves') == 'True'

    def _default_cancel_workorder(self):
        """Return default value from configuration settings."""
        return self.env['ir.config_parameter'].sudo().get_str(
            'cancel_mo.is_cancel_workorder') == 'True'

    cancel_inventory_moves = fields.Boolean(
        default=lambda self: self._default_cancel_inventory(),
        help="Whether to cancel the inventory moves")
    cancel_workorder = fields.Boolean(
        string="Cancel Work Orders",
        default=lambda self: self._default_cancel_workorder(),
        help="Whether to cancel the work orders")
    is_cancelled = fields.Boolean(
        copy=False,
        default=False,
        index=True,
        help="Technical flag indicating the manufacturing order has been cancelled.",
    )

    @api.depends('is_cancelled')
    def _compute_state(self):
        res = super()._compute_state()
        for production in self:
            if production.is_cancelled:
                production.state = 'cancel'
        return res

    def write(self, vals):
        """Synchronize is_cancelled technical flag with state changes."""
        if vals.get('state') == 'cancel':
            vals['is_cancelled'] = True
        elif 'state' in vals and vals['state'] != 'cancel':
            vals['is_cancelled'] = False
        return super().write(vals)

    def action_cancel_mo(self):
        """Cancels the manufacturing order in done state and reverts
        inventory/work orders if configured."""
        if not self.env.user.has_group('mrp.group_mrp_manager'):
            raise AccessError(
                self.env._("Only Manufacturing Managers can cancel done manufacturing orders.")
            )
        _logger.info("action_cancel_mo triggered for MO ids: %s", self.ids)
        for production in self:
            if production.state != 'done':
                continue

            cancel_inventory = production.cancel_inventory_moves
            cancel_workorder = production.cancel_workorder

            if cancel_inventory and production.qty_produced > 0:
                unbuild_vals = {
                    'mo_id': production.id,
                    'product_id': production.product_id.id,
                    'product_qty': production.qty_produced,
                    'company_id': production.company_id.id,
                    'location_id': production.location_dest_id.id,
                    'location_dest_id': production.location_src_id.id,
                }
                if production.lot_producing_ids:
                    unbuild_vals['lot_ids'] = [fields.Command.set(production.lot_producing_ids.ids)]
                unbuild = self.env['mrp.unbuild'].create(unbuild_vals)
                unbuild.action_unbuild()

            open_moves = (production.move_raw_ids | production.move_finished_ids).filtered(
                lambda m: m.state not in ('done', 'cancel')
            )
            if open_moves:
                open_moves.with_context(skip_mo_check=True)._action_cancel()

            open_pickings = production.picking_ids.filtered(
                lambda p: p.state not in ('done', 'cancel')
            )
            if open_pickings:
                open_pickings.action_cancel()

            if cancel_workorder:
                production.workorder_ids.filtered(
                    lambda w: w.state != 'cancel'
                ).action_cancel()

            production.write({
                'is_cancelled': True,
                'state': 'cancel',
            })
        return True

    def action_cancel(self):
        """Cancels manufacturing orders, delegating done MOs to action_cancel_mo
        and calling super().action_cancel() for non-done MOs."""
        done_mos = self.filtered(lambda mo: mo.state == 'done')
        non_done_mos = self - done_mos
        res = True
        if non_done_mos:
            res = super(MrpProduction, non_done_mos).action_cancel()
        if done_mos:
            res = done_mos.action_cancel_mo() and res
        return res

    def _action_cancel(self):
        """Cancels manufacturing orders, delegating done MOs to action_cancel_mo
        and delegating non-done MOs to super()._action_cancel() or super().action_cancel()."""
        done_mos = self.filtered(lambda mo: mo.state == 'done')
        non_done_mos = self - done_mos
        res = True
        if non_done_mos:
            if hasattr(super(MrpProduction, non_done_mos), '_action_cancel'):
                res = super(MrpProduction, non_done_mos)._action_cancel()
            else:
                # Fallback if base class does not define private cancel
                res = super(MrpProduction, non_done_mos).action_cancel()  # pylint: disable=super-method-mismatch
        if done_mos:
            res = done_mos.action_cancel_mo() and res
        return res

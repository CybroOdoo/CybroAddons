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
#############################################################################
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    is_partially_produced = fields.Boolean(
        string='Components Consumed', default=False, copy=False)
    is_finalized = fields.Boolean(
        string='Finished', default=False, copy=False)

    @api.depends('move_raw_ids.state', 'move_finished_ids.state')
    def _compute_state(self):
        for order in self:
            # Preserve Odoo's original computation for most cases
            super(MrpProduction, order)._compute_state()
            # If components are consumed but finished not yet, force ``progress``
            if order.is_partially_produced and order.state == 'to_close' or (
                    not order.is_finalized and order.state == 'to_close'):
                order.state = 'progress'

    def _check_sn_uniqueness(self):
        """ Alert the user if the serial number as already been consumed/produced """
        skip_consumption_sn =  self.env.context.get('skip_consumption_sn', False)
        if self.product_tracking == 'serial' and self.lot_producing_id:
            if self._is_finished_sn_already_produced(self.lot_producing_id):
                raise UserError(_('This serial number for product %s has already been produced', self.product_id.name))
        for move in self.move_finished_ids:
            if move.has_tracking != 'serial' or move.product_id == self.product_id:
                continue
            for move_line in move.move_line_ids:
                if float_is_zero(move_line.quantity, precision_rounding=move_line.product_uom_id.rounding):
                    continue
                if self._is_finished_sn_already_produced(move_line.lot_id, excluded_sml=move_line):
                    raise UserError(
                        _('The serial number %(number)s used for byproduct %(product_name)s has already been produced',
                          number=move_line.lot_id.name, product_name=move_line.product_id.name))
        consumed_sn_ids = []
        sn_error_msg = {}
        if not skip_consumption_sn:
            for move in self.move_raw_ids:
                if move.has_tracking != 'serial' or not move.picked:
                    continue
                for move_line in move.move_line_ids:
                    if not move_line.picked or float_is_zero(move_line.quantity,
                                                             precision_rounding=move_line.product_uom_id.rounding):
                        continue
                    sml_sn = move_line.lot_id
                    message = _('The serial number %(number)s used for component %(component)s has already been consumed',
                                number=sml_sn.name,
                                component=move_line.product_id.name)
                    consumed_sn_ids.append(sml_sn.id)
                    sn_error_msg[sml_sn.id] = message
                    co_prod_move_lines = self.move_raw_ids.move_line_ids
                    duplicates = co_prod_move_lines.filtered(lambda ml: ml.quantity and ml.lot_id == sml_sn) - move_line
                    if duplicates:
                        raise UserError(message)
        if not consumed_sn_ids:
            return
        consumed_sml_groups = self.env['stock.move.line']._read_group([
            ('lot_id', 'in', consumed_sn_ids),
            ('quantity', '=', 1),
            ('state', '=', 'done'),
            ('location_dest_id.usage', '=', 'production'),
            ('production_id', '!=', False),
        ], ['lot_id'], ['quantity:sum'])
        consumed_qties = {lot.id: qty for lot, qty in consumed_sml_groups}
        problematic_sn_ids = list(consumed_qties.keys())
        if not problematic_sn_ids:
            return
        cancelled_sml_groups = self.env['stock.move.line']._read_group([  # SML that cancels the SN consumption
            ('lot_id', 'in', problematic_sn_ids),
            ('quantity', '=', 1),
            ('state', '=', 'done'),
            ('location_id.usage', '=', 'production'),
            ('move_id.production_id', '=', False),
        ], ['lot_id'], ['quantity:sum'])
        cancelled_qties = defaultdict(float, {lot.id: qty for lot, qty in cancelled_sml_groups})
        for sn_id in problematic_sn_ids:
            consumed_qty = consumed_qties[sn_id]
            cancelled_qty = cancelled_qties[sn_id]
            if consumed_qty - cancelled_qty > 0:
                raise UserError(sn_error_msg[sn_id])

    def action_produce_all_custom(self):
        """Consume raw component moves without creating finished‑product moves.
        The method mirrors Odoo's native consumption flow:
        * it uses ``raw_moves._action_done()`` which handles back‑orders,
          work‑order linking, serial‑number checks, etc.
        * it then forces the form view to reload so the button visibility
          (controlled by the XML view) is recomputed instantly.
        """
        self.ensure_one()
        if self.state not in ('confirmed', 'progress'):
            raise UserError(_(
                'Manufacturing order must be confirmed or in progress to consume components.'
            ))
        self._button_mark_done_sanity_checks()
        for production in self:
            if float_is_zero(production.qty_producing, precision_rounding=production.product_uom_id.rounding):
                production._set_quantities()
        for production in self:
            if float_is_zero(production.qty_producing, precision_rounding=production.product_uom_id.rounding):
                raise UserError(_('The quantity to produce must be positive!'))
        consumption_issues = self._get_consumption_issues()
        if consumption_issues:
            return self._action_generate_consumption_wizard(consumption_issues)
        # If additional MRP-related modules are installed and introduce
        # extra validations or processing during production completion,
        # their relevant consumption-side logic should be included here.
        #
        # Since `pre_button_mark_done()` also contains finished-product
        # validations and backorder-related flows, it cannot be reused
        # directly for the consumption completion step of the split workflow.
        #
        # Therefore, module-specific consumption validations are handled
        # explicitly here whenever required. For example, the expiry
        # validation from `mrp_expiry` has been replicated below to ensure
        # expired component checks are still enforced during the
        # consumption confirmation stage.
        #
        # Future module integrations should follow the same approach by
        # conditionally extending this section based on installed modules.
        def is_module_installed(self, module_name):
            """checking if the module is installed or not"""
            return self.env['ir.module.module'].search_count([
                ('name', '=', module_name),
                ('state', 'in', ['installed', 'to upgrade'])
            ]) > 0
        # adding the code from the mrp_expiry module hardcoded if they are installed
        mrp_expiry_installed = is_module_installed(self, 'mrp_expiry')
        if mrp_expiry_installed:
            confirm_expired_lots = self._check_expired_lots()
            if confirm_expired_lots:
                return confirm_expired_lots
        # adding the code from the mrp_workorder module hardcoded if they are installed
        mrp_workorder_installed = is_module_installed(self, 'mrp_workorder')
        if mrp_workorder_installed:
            self.workorder_ids.verify_quality_checks()
            self.workorder_ids.button_finish()
        moves_to_do, moves_not_to_do, moves_to_cancel = set(), set(), set()
        for move in self.move_raw_ids:
            if move.state == 'done':
                moves_not_to_do.add(move.id)
            elif not move.picked:
                moves_to_cancel.add(move.id)
            elif move.state != 'cancel':
                moves_to_do.add(move.id)
        # skipping the backorder set up for now (for consumption) and will be carried on while finalising the
        # production
        self.with_context(skip_mo_check=True).env['stock.move'].browse(moves_to_do)._action_done(
            cancel_backorder=True)
        self.with_context(skip_mo_check=True).env['stock.move'].browse(moves_to_cancel)._action_cancel()
        # Mark that the components have been consumed
        self.is_partially_produced = True

    def action_finalize_mo(self):
        """Finalize the manufacturing order after components have been consumed.
        Calls the original ``button_mark_done`` which creates the finished‑product
        moves, posts stock, runs QC, work‑order completion, etc.
        """
        self.ensure_one()
        if not self.is_partially_produced:
            raise UserError(_(
                'You must consume components first using "Consume Components".'
            ))
        # passing the skip_consumption_sn True for neglecting the serial number usage check for components as they
        # already have gone through it
        res = super(MrpProduction, self).with_context(skip_consumption_sn=True).button_mark_done()
        if self.state == 'done':
            self.is_finalized = True
            # Reset the partial flag for potential reuse of the record
            self.is_partially_produced = False
        return res

    def _action_cancel(self):
        super(MrpProduction, self)._action_cancel()
        self.is_partially_produced = False
        self.is_finalized = False

# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = ['stock.picking', 'pos.load.mixin']

    is_click_and_collect_order = fields.Boolean(
        default=False,
        help='True when this transfer is a Click & Collect pickup order',
    )

    @api.model
    def _load_pos_data_domain(self, data, config):
        return []

    @api.model
    def _load_pos_data_fields(self, config_id):
        return []

    def _force_validate_picking(self, picking):
        """
        Reliably validate a picking to 'done' state in Odoo 19.

        Root cause of the silent failure: _action_done() with skip_backorder
        context does NOT work reliably for pickings that were created
        programmatically (not through the standard procurement wizard).
        The picking ends up in a state where _action_done() returns
        without error but leaves state = 'assigned'.

        Fix: use the proper public API sequence:
        1. action_assign()  — reserve stock, generate move_line_ids
        2. Set quantity on move lines
        3. with_context(skip_sms=True).button_validate() — triggers the
           full state machine including backorder checks, then immediately
           process the resulting wizard (if any) to skip backorders.
        """
        # Step 1 — reserve stock
        if picking.state not in ('assigned', 'done', 'cancel'):
            picking.action_assign()
            picking.invalidate_recordset()

        # Step 2 — set qty done = demand on every move and its move lines
        for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            move.quantity = move.product_uom_qty
            if not move.move_line_ids:
                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'picking_id': picking.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': move.product_uom_qty,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })
            else:
                for ml in move.move_line_ids:
                    ml.quantity = move.product_uom_qty

        # Step 3 — validate using button_validate() which drives the full
        # state machine correctly, then auto-confirm any backorder wizard
        try:
            result = picking.with_context(
                skip_sms=True,
                skip_backorder=True,
                picking_ids_not_to_backorder=picking.ids,
            ).button_validate()

            # button_validate() may return a wizard action instead of True
            # when it wants to ask about backorders. Handle both cases.
            if isinstance(result, dict) and result.get('res_model'):
                wizard_model = result['res_model']
                _logger.info("[CNC] button_validate returned wizard: %s", wizard_model)

                wizard_ctx = dict(result.get('context', {}))
                wizard = self.env[wizard_model].with_context(**wizard_ctx).create({})

                if hasattr(wizard, 'process'):
                    wizard.process()
                elif hasattr(wizard, 'action_generate_backorder'):
                    if hasattr(wizard, 'action_no_backorder'):
                        wizard.action_no_backorder()
                    else:
                        wizard.action_generate_backorder()
                elif hasattr(wizard, 'action_no_backorder'):
                    wizard.action_no_backorder()
                else:
                    wizard.process() if hasattr(wizard, 'process') else None

            picking.invalidate_recordset()

            if picking.state != 'done':
                _logger.warning(
                    "[CNC] picking id=%s still state=%s after button_validate, trying _action_done fallback",
                    picking.id, picking.state,
                )
                picking.with_context(
                    skip_backorder=True,
                    picking_ids_not_to_backorder=picking.ids,
                )._action_done()
                picking.invalidate_recordset()

        except Exception as e:
            _logger.error("[CNC] Exception validating picking id=%s: %s", picking.id, e, exc_info=True)
            raise

    @api.model
    def action_confirmation_click(self, sale_order_line_id):
        sale_order_line_id = int(sale_order_line_id)

        cac_picking = self.search([
            ('is_click_and_collect_order', '=', True),
            ('move_ids.sale_line_id', '=', sale_order_line_id),
            ('state', 'not in', ['done', 'cancel']),
        ], limit=1)

        if not cac_picking:
            _logger.warning("[CNC] No pending C&C picking for line id=%s", sale_order_line_id)
            return False

        self._force_validate_picking(cac_picking)
        if cac_picking.state != 'done':
            _logger.error("[CNC] Failed to validate C&C picking id=%s", cac_picking.id)
            return False

        sale_order = cac_picking.sale_id
        if not sale_order:
            return True

        normal_pickings = sale_order.picking_ids.filtered(
            lambda p: not p.is_click_and_collect_order
            and p.state not in ('done', 'cancel')
        )

        for normal_picking in normal_pickings:
            matched_moves = normal_picking.move_ids.filtered(
                lambda m: m.sale_line_id.id == sale_order_line_id
                and m.state not in ('done', 'cancel')
            )
            if not matched_moves:
                continue

            for move in matched_moves:
                move.quantity = move.product_uom_qty
                if not move.move_line_ids:
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'picking_id': normal_picking.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'quantity': move.product_uom_qty,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                    })
                else:
                    for ml in move.move_line_ids:
                        ml.quantity = move.product_uom_qty

            pending = normal_picking.move_ids.filtered(
                lambda m: m.state not in ('done', 'cancel')
                and m.quantity < m.product_uom_qty
            )

            if not pending:
                self._force_validate_picking(normal_picking)
                normal_picking.invalidate_recordset()
            else:
                _logger.info(
                    "[CNC] Normal picking id=%s has %s unfilled moves — leaving open",
                    normal_picking.id, len(pending),
                )

        return True

    @api.model
    def action_stock_picking(self, order_lines, pos_config_id=None):
        try:
            if pos_config_id:
                filtered_lines = self.env['sale.order.line'].browse(order_lines).filtered(
                    lambda l: l.pos_config_id.id == int(pos_config_id)
                )
                order_lines = filtered_lines.ids

            if not order_lines:
                return []

            records = []
            pending_pickings = self.search([
                ('state', 'not in', ('done', 'cancel')),
                ('is_click_and_collect_order', '=', True),
                ('move_ids.sale_line_id', 'in', order_lines),
            ])

            for picking in pending_pickings:
                for move in picking.move_ids:
                    if move.sale_line_id.id in order_lines:
                        records.append({
                            'id': move.sale_line_id.id,
                            'order_id': picking.origin or '',
                            'partner_id': picking.partner_id.name if picking.partner_id else '',
                            'product_id': move.product_id.name or '',
                            'product_uom_quantity': move.product_uom_qty,
                        })

            return records
        except Exception as exc:
            _logger.error("[CNC] action_stock_picking error: %s", exc, exc_info=True)
            return [{'error': str(exc)}]
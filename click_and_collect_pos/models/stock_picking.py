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

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """Extend stock picking for Click & Collect order handling."""
    _inherit = 'stock.picking'

    is_click_and_collect_order = fields.Boolean(
        string='Click & Collect Transfer',
        default=False,
        help='True when this transfer is a Click & Collect pickup order.',
    )

    def _force_validate_picking(self, picking):
        """Validate a picking to 'done' state reliably."""
        picking = picking.sudo()
        if picking.state not in ('assigned', 'done', 'cancel'):
            picking.action_assign()
            picking.invalidate_recordset()

        for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            move.quantity = move.product_uom_qty
            if not move.move_line_ids:
                self.env['stock.move.line'].sudo().create({
                    'move_id': move.id,
                    'picking_id': picking.id,
                    'product_id': move.product_id.id,
                    'uom_id': move.uom_id.id,
                    'quantity': move.product_uom_qty,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                })
            else:
                for ml in move.move_line_ids:
                    ml.quantity = move.product_uom_qty

        try:
            result = picking.with_context(
                skip_sms=True,
                skip_backorder=True,
                picking_ids_not_to_backorder=picking.ids,
            ).button_validate()

            if isinstance(result, dict) and result.get('res_model'):
                wizard_model = result['res_model']
                wizard_ctx = dict(result.get('context', {}))
                wizard = self.env[wizard_model].sudo().with_context(**wizard_ctx).create({})
                if hasattr(wizard, 'process'):
                    wizard.process()
                elif hasattr(wizard, 'action_no_backorder'):
                    wizard.action_no_backorder()
                elif hasattr(wizard, 'action_generate_backorder'):
                    wizard.action_generate_backorder()

            picking.invalidate_recordset()

            if picking.state != 'done':
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
        """Validate the Click & Collect picking for a sale order line.

        In multi-step delivery routes (e.g. pick -> pack -> out), completing an
        upstream picking automatically pushes moves to the next downstream step.
        We iteratively validate pickings until all chained moves for the order line
        reach the customer location and are marked 'done'.
        """
        sale_order_line_id = int(sale_order_line_id)
        line = self.env['sale.order.line'].sudo().browse(sale_order_line_id)
        if not line.exists():
            _logger.warning("[CNC] Sale order line id=%s not found", sale_order_line_id)
            return False

        validated_any = False
        max_steps = 10  # Protection against infinite loops
        for _ in range(max_steps):
            direct_moves = line.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
            orig_move_ids = direct_moves._rollup_move_origs()
            dest_move_ids = direct_moves._rollup_move_dests()
            all_moves = direct_moves | self.env['stock.move'].sudo().browse(
                orig_move_ids | dest_move_ids
            ).filtered(lambda m: m.state not in ('done', 'cancel'))

            cac_pickings = all_moves.mapped('picking_id').filtered(
                lambda p: p.state not in ('done', 'cancel')
            )
            if not cac_pickings:
                cac_pickings = self.sudo().search([
                    ('is_click_and_collect_order', '=', True),
                    ('move_ids.sale_line_id', '=', sale_order_line_id),
                    ('state', 'not in', ['done', 'cancel']),
                ])

            if not cac_pickings:
                break

            for p in cac_pickings:
                if not p.is_click_and_collect_order:
                    p.is_click_and_collect_order = True

            # In multi-step delivery (e.g. pick -> out), validate upstream pickings first
            def picking_order(p):
                has_dest = any(m.move_dest_ids for m in p.move_ids)
                is_customer = p.location_dest_id.usage == 'customer'
                if has_dest and not is_customer:
                    return 0  # upstream (Pick / Pack)
                return 1      # downstream (Delivery / Customer)

            next_picking = cac_pickings.sorted(key=picking_order)[0]
            self._force_validate_picking(next_picking.sudo())
            validated_any = True

        if validated_any:
            self.env["bus.bus"]._sendone(
                'POS_COLLECT_ORDER',
                'POS_COLLECT_ORDER',
                {"order_line_id": sale_order_line_id, "status": "done"},
            )

        return validated_any

    @api.model
    def action_stock_picking(self, order_lines, pos_config_id=None):
        """Return pending Click & Collect picking details for order lines."""
        try:
            if pos_config_id:
                filtered_lines = self.env['sale.order.line'].sudo().browse(order_lines).filtered(
                    lambda l: not l.pos_config_id or l.pos_config_id.id == int(pos_config_id)
                )
                order_lines = filtered_lines.ids

            if not order_lines:
                return []

            records = []
            pending_pickings = self.sudo().search([
                ('state', 'not in', ('done', 'cancel')),
                ('is_click_and_collect_order', '=', True),
                ('move_ids.sale_line_id', 'in', order_lines),
            ])

            seen_line_ids = set()
            for picking in pending_pickings:
                for move in picking.move_ids:
                    line_id = move.sale_line_id.id
                    if line_id in order_lines and line_id not in seen_line_ids:
                        seen_line_ids.add(line_id)
                        records.append({
                            'id': line_id,
                            'order_id': picking.origin or move.sale_line_id.order_id.name or '',
                            'partner_id': picking.partner_id.name if picking.partner_id else '',
                            'product_id': move.product_id.name or '',
                            'product_uom_quantity': move.product_uom_qty,
                        })

            return records
        except Exception as exc:
            _logger.error("[CNC] action_stock_picking error: %s", exc, exc_info=True)
            return [{'error': str(exc)}]
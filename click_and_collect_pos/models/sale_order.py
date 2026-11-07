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


class SaleOrder(models.Model):
    """Inherit sale order to manage Click & Collect pickings and smart buttons."""
    _inherit = 'sale.order'

    collect_count = fields.Integer(
        string='Click & Collect',
        compute='_compute_collect_count',
        help='Count of Click & Collect pickings linked to this sale order.',
    )

    @api.depends('picking_ids', 'picking_ids.is_click_and_collect_order')
    def _compute_picking_ids(self):
        """Override delivery count to exclude Click & Collect pickings."""
        res = super()._compute_picking_ids()
        for order in self:
            filtered_pickings = order.picking_ids.filtered(
                lambda p: not p.is_click_and_collect_order)
            order.delivery_count = len(filtered_pickings)
        return res

    def _get_action_view_picking(self, pickings):
        """Return action for delivery smart button, excluding C&C pickings."""
        filtered_pickings = pickings.filtered(lambda p: not p.is_click_and_collect_order)
        if not filtered_pickings:
            action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
            action['domain'] = [('id', 'in', [])]
            action['context'] = {'default_partner_id': self.partner_id.id}
            return action
        return super()._get_action_view_picking(filtered_pickings)

    @api.depends('picking_ids', 'picking_ids.is_click_and_collect_order')
    def _compute_collect_count(self):
        """Count Click & Collect pickings for the smart button."""
        for order in self:
            order.collect_count = len(order.picking_ids.filtered(
                lambda p: p.is_click_and_collect_order))

    def _action_confirm(self):
        """Confirm order and split Click & Collect lines into dedicated pickings."""
        result = super()._action_confirm()
        self._prepare_cac_split()
        return result

    def _prepare_cac_split(self):
        """Create dedicated C&C picking for each C&C order line by reassigning
        the existing stock moves created during order confirmation, ensuring
        no duplicate moves or double stock deduction occurs, and preserving
        multi-step delivery move chains."""
        for order in self:
            click_and_collect_lines = order.order_line.filtered(
                lambda l: l.is_click_and_collect)

            if not click_and_collect_lines:
                continue

            # Notify open POS sessions about new C&C orders
            pos_configs = click_and_collect_lines.pos_config_id or self.env['pos.config'].search([
                ('company_id', '=', order.company_id.id)
            ])
            for config in pos_configs:
                config._notify('POS_COLLECT_ORDER', {
                    'order_id': order.id,
                    'order_name': order.name,
                })
            self.env["bus.bus"]._sendone(
                'POS_COLLECT_ORDER',
                'POS_COLLECT_ORDER',
                {"order_id": order.id, "order_name": order.name},
            )

            # In multi-step delivery routes (e.g. pick -> pack -> out),
            # upstream moves (move_orig_ids) don't have sale_line_id directly set.
            # We group C&C moves by pickup store (pos_config_id) so each store gets
            # its own dedicated picking, preserving multi-step delivery move chains.
            lines_by_store = click_and_collect_lines.grouped('pos_config_id')
            for _store, store_lines in lines_by_store.items():
                store_direct_moves = store_lines.move_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel')
                )
                if not store_direct_moves:
                    continue

                orig_move_ids = store_direct_moves._rollup_move_origs()
                dest_move_ids = store_direct_moves._rollup_move_dests()
                store_cac_moves = store_direct_moves | self.env['stock.move'].browse(
                    orig_move_ids | dest_move_ids
                ).filtered(lambda m: m.state not in ('done', 'cancel'))

                existing_pickings = store_cac_moves.mapped('picking_id')
                for picking in existing_pickings:
                    picking_store_moves = picking.move_ids & store_cac_moves
                    remaining_moves = picking.move_ids - store_cac_moves

                    if not remaining_moves:
                        # If all moves in the picking belong to this C&C store, mark it directly
                        picking.is_click_and_collect_order = True
                    else:
                        # Split store C&C moves into a new picking of identical type and locations
                        cac_picking = picking.copy({
                            'move_ids': [],
                            'is_click_and_collect_order': True,
                        })
                        picking_store_moves.write({'picking_id': cac_picking.id})

                # In case any C&C moves were not assigned to any picking yet:
                unassigned_cac_moves = store_cac_moves.filtered(lambda m: not m.picking_id)
                if unassigned_cac_moves:
                    for move in unassigned_cac_moves:
                        cac_picking = self.env['stock.picking'].create({
                            'partner_id': order.partner_shipping_id.id or order.partner_id.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'picking_type_id': move.picking_type_id.id,
                            'sale_id': order.id,
                            'origin': order.name,
                            'company_id': order.company_id.id,
                            'is_click_and_collect_order': True,
                        })
                        move.write({'picking_id': cac_picking.id})

    def action_view_click_and_collect(self):
        """Open the Click & Collect pickings list from the smart button."""
        self.ensure_one()
        pickings = self.picking_ids.filtered(lambda p: p.is_click_and_collect_order)
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        else:
            action['domain'] = [('id', 'in', [])]
        action['name'] = 'Click & Collect'
        action['context'] = {'create': False}
        return action
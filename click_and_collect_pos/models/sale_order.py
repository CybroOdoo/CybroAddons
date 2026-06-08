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


class SaleOrder(models.Model):
    """Inherited to handle Click & Collect splitting and smart button display.

    Workflow:
    - On confirm, the native Odoo delivery is created for ALL lines.
    - For C&C lines, a separate C&C picking is ALSO created (Ready state).
    - The normal delivery keeps its C&C line moves BUT is also kept alive
      so both normal delivery AND C&C picking are in Ready state.
    - When the cashier confirms from POS, action_confirmation_click validates
      the C&C picking AND the normal delivery together → both go to Done.
    """
    _inherit = 'sale.order'

    collect_count = fields.Integer(
        string='Click And Collect',
        compute='_compute_collect_count',
        help='Count of Click & Collect pickings linked to this sale order',
    )

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        """Override delivery count to exclude Click & Collect pickings."""
        for order in self:
            filtered_pickings = order.picking_ids.filtered(
                lambda p: not p.is_click_and_collect_order)
            order.delivery_count = len(filtered_pickings)

    def _get_action_view_picking(self, pickings):
        """Return action for delivery smart button, excluding C&C pickings."""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all")
        pickings = pickings.filtered(
            lambda p: not p.is_click_and_collect_order)
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view)
                    for state, view in action['views']
                    if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        picking_id = pickings.filtered(
            lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        elif pickings:
            picking_id = pickings[0]
        else:
            return action
        action['context'] = dict(
            default_partner_id=self.partner_id.id,
            default_picking_type_id=picking_id.picking_type_id.id,
            default_origin=self.name,
        )
        return action

    @api.depends('picking_ids')
    def _compute_collect_count(self):
        """Count Click & Collect pickings for the smart button."""
        for order in self:
            order.collect_count = self.env['stock.picking'].search_count([
                ('is_click_and_collect_order', '=', True),
                ('origin', '=', order.name),
            ])

    def _action_confirm(self):
        """Override _action_confirm:
        1. Run Odoo's native confirm — creates the normal delivery (Ready).
        2. Create additional dedicated C&C pickings (also Ready).
        Both pickings stay alive. POS confirms both together.
        """
        result = super(SaleOrder, self)._action_confirm()
        self._prepare_cac_split()
        return result

    def _prepare_cac_split(self):
        """Create one dedicated C&C picking per C&C order line.

        The normal delivery created by Odoo is left untouched (stays Ready).
        A separate C&C picking is created for each C&C line so the POS
        cashier can see and confirm the pickup. When confirmed from POS,
        action_confirmation_click validates BOTH the C&C picking and the
        corresponding move in the normal delivery.
        """
        click_and_collect_lines = self.order_line.filtered(
            lambda l: l.is_click_and_collect)

        if not click_and_collect_lines:
            return

        # Notify any open POS session about new C&C orders
        self.env["bus.bus"]._sendone(
            'POS_COLLECT_ORDER',
            "notification",
            {"channel": 'POS_COLLECT_ORDER'},
        )

        # Use the warehouse output / stock location as source
        warehouse = self.warehouse_id or self.env['stock.warehouse'].search(
            [('company_id', '=', self.company_id.id)], limit=1)
        src_location = (warehouse.lot_stock_id if warehouse
                        else self.env.ref('stock.stock_location_stock'))
        dest_location = self.env.ref('stock.stock_location_customers')
        picking_type = self.env.ref('stock.picking_type_out')

        for line in click_and_collect_lines:
            picking = self.env['stock.picking'].create({
                'partner_id': self.partner_id.id,
                'location_id': src_location.id,
                'location_dest_id': dest_location.id,
                'picking_type_id': picking_type.id,
                'sale_id': self.id,
                'origin': self.name,
                'is_click_and_collect_order': True,
            })
            move = self.env['stock.move'].create({
                'display_name': line.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom_id.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'sale_line_id': line.id,
            })
            move._action_confirm()

    # Kept for backward compatibility
    def action_split_delivery_order(self):
        self._prepare_cac_split()
        return True

    def action_view_click_and_collect(self):
        """Open the Click & Collect pickings list from the smart button."""
        self.ensure_one()
        return {
            'name': 'Click And Collect',
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [
                ('origin', '=', self.name),
                ('is_click_and_collect_order', '=', True),
            ],
            'context': "{'create':False}",
        }
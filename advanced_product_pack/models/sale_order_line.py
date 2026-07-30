# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import api, fields, models
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    """Extension of sale.order.line to support bundle product explosion into components."""

    _inherit = 'sale.order.line'

    is_pack_component = fields.Boolean(
        string='Is Pack Component',
        help='Technical field to identify service lines created from bundle explosion.',
    )

    @api.depends('move_ids.state', 'move_ids.scrapped',
                 'move_ids.quantity', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        """Compute delivered qty for bundle lines based on component moves."""
        bundle_lines = self.filtered(
            lambda l: l.product_id.is_bundle and not l.is_pack_component
        )
        super(SaleOrderLine, self - bundle_lines)._compute_qty_delivered()
        for line in bundle_lines:
            # Get all done moves linked to this SOL
            done_moves = line.move_ids.filtered(
                lambda m: m.state == 'done' and not m.scrapped
            )
            if not done_moves or not line.product_id.bundle_line_ids:
                line.qty_delivered = 0.0
                continue
            # Calculate ratio: min of (delivered / expected) across components
            ratios = []
            for bundle_item in line.product_id.bundle_line_ids:
                if bundle_item.product_id.type == 'service':
                    continue
                expected_qty = bundle_item.quantity * line.product_uom_qty
                if expected_qty <= 0:
                    continue
                delivered = sum(
                    m.product_uom._compute_quantity(m.quantity, m.product_uom)
                    for m in done_moves
                    if m.product_id == bundle_item.product_id
                )
                ratios.append(delivered / expected_qty)
            if ratios:
                line.qty_delivered = min(ratios) * line.product_uom_qty
            else:
                line.qty_delivered = 0.0

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """Explode bundle products into their components during stock rule launch.

        Storables: Create direct moves.
        Services: Create shadow SOLs to trigger project/task generation.
        """
        if self.env.context.get('skip_procurement'):
            return True

        precision = self.env['decimal.precision'].precision_get('Product Unit')
        # Skip explosion for lines that are already components to avoid recursion
        bundle_lines = self.filtered(lambda l: l.product_id.is_bundle and not l.is_pack_component)
        other_lines = self - bundle_lines

        # 1. Handle regular (non-bundle) lines via super
        if other_lines:
            super(SaleOrderLine, other_lines)._action_launch_stock_rule(
                previous_product_uom_qty=previous_product_uom_qty
            )

        # 2. Handle bundle lines
        for line in bundle_lines:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or line.order_id.locked:
                continue

            # Check if procurement is already done for this line
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
                continue


            # Picking for storable components
            picking = line.order_id.picking_ids.filtered(
                lambda p: p.state not in ['cancel', 'done']
            )[:1]

            for bundle_item in line.product_id.bundle_line_ids:
                component_product = bundle_item.product_id
                component_qty = bundle_item.quantity * (line.product_uom_qty - qty)

                if float_compare(component_qty, 0, precision_digits=precision) <= 0:
                    continue

                if component_product.type != 'service':
                    # Storable/Consumable: Create Move
                    if not picking:
                        addr = line.order_id.partner_shipping_id
                        picking_values = {
                            'partner_id': addr.id,
                            'user_id': line.order_id.user_id.id,
                            'picking_type_id': line.warehouse_id.out_type_id.id,
                            'location_id': line.warehouse_id.lot_stock_id.id,
                            'location_dest_id': addr.property_stock_customer.id,
                            'origin': line.order_id.name,
                            'move_type': line.order_id.picking_policy,
                            'company_id': line.company_id.id,
                            'sale_id': line.order_id.id,
                        }
                        picking = self.env['stock.picking'].sudo().create(picking_values)

                    move_vals = {
                        'name': component_product.display_name,
                        'product_id': component_product.id,
                        'product_uom_qty': component_qty,
                        'product_uom': component_product.uom_id.id,
                        'location_id': line.warehouse_id.lot_stock_id.id,
                        'location_dest_id': line.order_id.partner_shipping_id.property_stock_customer.id,
                        'picking_id': picking.id,
                        'sale_line_id': line.id,
                        'warehouse_id': line.warehouse_id.id,
                        'procure_method': 'make_to_stock',
                        'company_id': line.company_id.id,
                        'origin': line.order_id.name,
                        'picking_type_id': line.warehouse_id.out_type_id.id,
                    }
                    move = self.env['stock.move'].sudo().create(move_vals)
                    move._action_confirm()
                    move._action_assign()
                else:
                    # Service: Create shadow SOL to trigger project/task creation
                    new_line = self.env['sale.order.line'].sudo().with_context(
                        skip_procurement=True
                    ).create({
                        'order_id': line.order_id.id,
                        'product_id': component_product.id,
                        'product_uom_qty': component_qty,
                        'product_uom': component_product.uom_id.id,
                        'price_unit': 0.0,
                        'is_pack_component': True,
                        'state': 'sale',
                    })
                    if new_line.task_id:
                        new_line.task_id.write({'state': '00_new'})

        return True

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
from odoo import models


class StockPicking(models.Model):
    """Inheriting the stock_picking model and creating the stock move from point of sale."""
    _inherit = 'stock.picking'

    def _create_move_from_pos_order_lines(self, lines):
        """Create component moves alongside the regular POS stock moves."""
        self.ensure_one()
        existing_move_ids = set(self.move_ids.ids)
        result = super()._create_move_from_pos_order_lines(lines)
        pos_moves = self.move_ids.filtered(lambda move: move.id not in existing_move_ids)

        line_groups = lines.grouped(lambda line: (
            line.product_id.id,
            tuple(sorted(line.attribute_value_ids.ids)),
        ))
        for move in pos_moves.filtered(lambda move: move.product_id.is_bom):
            bom = self.env['pos.product.bom'].search([
                ('product_id', '=', move.product_id.product_tmpl_id.id),
            ], limit=1)
            if not bom or not bom.quantity:
                continue
            group_key = (
                move.product_id.id,
                tuple(sorted(move.never_product_template_attribute_value_ids.ids)),
            )
            order_lines = line_groups.get(group_key)
            if not order_lines:
                order_lines = lines.filtered(
                    lambda line: line.product_id == move.product_id
                    and set(line.attribute_value_ids.filtered(
                        lambda value: value.attribute_id.create_variant == 'no_variant'
                    ).ids) == set(move.never_product_template_attribute_value_ids.ids)
                )
            sold_quantity = abs(sum(
                line._get_qty_to_move() for line in order_lines
            ))
            component_moves = self.env['stock.move']
            for component in bom.bom_line_ids:
                quantity = sold_quantity * component.quantity / bom.quantity
                if not quantity:
                    continue
                component_moves |= self.env['stock.move'].create({
                    'date': self.create_date,
                    'uom_id': component.product_uom_id.id or component.product_id.uom_id.id,
                    'picking_id': self.id,
                    'picking_type_id': self.picking_type_id.id,
                    'product_id': component.product_id.id,
                    'product_uom_qty': quantity,
                    'warehouse_id': self.location_id.warehouse_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'company_id': self.company_id.id,
                })
            component_moves._action_confirm()
            for component_move in component_moves:
                component_move.quantity = component_move.product_uom_qty
                component_move.picked = True
        return result

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models

from itertools import groupby


class StockPicking(models.Model):
    """Inheriting the stock_picking model and creating the stock move from point of sale."""
    _inherit = 'stock.picking'

    def _create_move_from_pos_order_lines(self, lines):
        """Create stock move from point of sale"""

        self.ensure_one()
        lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
        move_vals = []
        for dummy, olines in lines_by_product:
            order_lines = self.env['pos.order.line'].concat(*olines)
            move_vals.append(self._prepare_stock_move_vals(order_lines[0], order_lines))
        moves = self.env['stock.move'].create(move_vals)
        confirmed_moves = moves._action_confirm()
        for move in confirmed_moves:
            if move.product_id.is_bom:
                products = self.env['pos.product.bom'].search(
                    [('product_id.id', '=',
                      move.product_id.product_tmpl_id.id)])
                for rec in products.bom_line_ids:
                    pos_bom_move = self.env['stock.move'].create(
                        {
                            'name': self.name,
                            'date': self.create_date,
                            'product_uom': rec.product_uom_id.id,
                            'picking_id': self.id,
                            'picking_type_id': self.picking_type_id.id,
                            'product_id': rec.product_id.id,
                            'product_uom_qty': abs(sum(order_lines.mapped(
                                'qty'))) * (rec.quantity / products.quantity),
                            'state': 'done',
                            'warehouse_id': self.location_dest_id.warehouse_id.id,
                            'location_id': self.location_id.id,
                            'location_dest_id': self.location_dest_id.id,
                            'company_id': self.company_id.id,
                        }
                    )
                    pos_bom_move.quantity = pos_bom_move.product_uom_qty
        confirmed_moves._add_mls_related_to_order(lines, are_qties_done=True)
        confirmed_moves.picked = True

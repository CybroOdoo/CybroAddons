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

from itertools import groupby

from odoo import  models


class StockPicking(models.Model):
    """Extension of stock.picking to explode bundle products into components for PoS pickings."""

    _inherit = 'stock.picking'

    def _create_move_from_pos_order_lines(self, lines):
        """Override to explode bundle products into their components for PoS pickings."""
        self.ensure_one()

        move_vals = []
        regular_lines = self.env['pos.order.line']

        for line in lines:
            if line.product_id.is_bundle and line.product_id.bundle_line_ids:
                # Explode bundle into components
                for pack_line in line.product_id.bundle_line_ids:
                    if pack_line.product_id.type == 'service':
                        continue
                    # Construct move values for each component
                    move_vals.append({
                        'name': pack_line.product_id.display_name,
                        'product_uom': pack_line.product_id.uom_id.id,
                        'picking_id': self.id,
                        'picking_type_id': self.picking_type_id.id,
                        'product_id': pack_line.product_id.id,
                        'product_uom_qty': abs(line.qty * pack_line.quantity),
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'company_id': self.company_id.id,
                        'origin': self.origin,
                    })
            else:
                regular_lines |= line

        def get_grouping_key(line):
            return (line.product_id.id, tuple(sorted(line.attribute_value_ids.ids)))

        lines_by_product_and_attrs = groupby(
            sorted(regular_lines, key=get_grouping_key),
            key=get_grouping_key,
        )
        for _product, olines in lines_by_product_and_attrs:
            order_lines = self.env['pos.order.line'].concat(*olines)
            move_vals.append(self._prepare_stock_move_vals(order_lines[0], order_lines))

        moves = self.env['stock.move'].create(move_vals)
        confirmed_moves = moves._action_confirm()


        confirmed_moves._add_mls_related_to_order(lines, are_qties_done=True)

        confirmed_moves.picked = True

        self._link_owner_on_return_picking(lines)

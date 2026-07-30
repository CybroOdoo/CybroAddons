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


class PosOrderLine(models.Model):
    """Extension of pos.order.line to explode bundle products for 'ship later' PoS orders."""

    _inherit = 'pos.order.line'

    def _launch_stock_rule_from_pos_order_lines(self):
        """Override to explode bundle products for 'ship later' PoS orders."""
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.product_id.type != 'consu':
                continue

            if line.product_id.is_bundle and line.product_id.product_tmpl_id.bundle_line_ids:
                for pack_line in line.product_id.product_tmpl_id.bundle_line_ids:
                    if pack_line.product_id.type == 'service':
                        continue

                    values = line._prepare_procurement_values()
                    product_qty = abs(line.qty * pack_line.quantity)
                    procurement_uom = pack_line.product_id.uom_id

                    procurements.append(self.env['stock.rule'].Procurement(
                        pack_line.product_id, product_qty, procurement_uom,
                        line.order_id.partner_id.property_stock_customer,
                        pack_line.product_id.display_name, line.order_id.name, line.order_id.company_id, values,
                    ))
            else:
                values = line._prepare_procurement_values()
                product_qty = line.qty
                procurement_uom = line.product_id.uom_id

                procurements.append(self.env['stock.rule'].Procurement(
                    line.product_id, product_qty, procurement_uom,
                    line.order_id.partner_id.property_stock_customer,
                    line.product_id.display_name, line.order_id.name, line.order_id.company_id, values,
                ))

        if procurements:
            self.env['stock.rule'].run(procurements)

        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(
                lambda p: p.state not in ['done', 'cancel']
            )
            if pickings_to_confirm:
                tracked_lines = order.lines.filtered(lambda l: l.product_id.tracking != 'none')
                lines_by_tracked_product = groupby(
                    sorted(tracked_lines, key=lambda l: l.product_id.id),
                    key=lambda l: l.product_id.id,
                )
                pickings_to_confirm.action_confirm()
                for product_id, lines in lines_by_tracked_product:
                    lines = self.env['pos.order.line'].concat(*lines)
                    moves = pickings_to_confirm.move_ids.filtered(
                        lambda m: m.product_id.id == product_id
                    )
                    moves.move_line_ids.unlink()
                    moves._add_mls_related_to_order(lines, are_qties_done=False)
                    moves._recompute_state()
        return True

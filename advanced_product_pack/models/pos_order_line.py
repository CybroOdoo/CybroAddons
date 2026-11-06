###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
# pylint: disable=missing-module-docstring,unknown-option-value,too-few-public-methods,protected-access,too-many-locals,bad-builtin-groupby
from itertools import groupby

from odoo import models
from odoo.fields import Command


class PosOrderLine(models.Model):
    """Extension of pos.order.line to explode bundle products for
    'ship later' PoS orders.
    """

    _inherit = 'pos.order.line'

    def _launch_stock_rule_from_pos_order_lines(self):
        """Override to explode bundle products for 'ship later' PoS orders."""
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.product_id.type != 'consu':
                continue

            # Identify if it's a bundle to explode
            tmpl = line.product_id.product_tmpl_id
            if line.product_id.is_bundle and tmpl.bundle_line_ids:
                for pack_line in tmpl.bundle_line_ids:
                    if pack_line.product_id.type == 'service':
                        continue
                    # Explode into component procurements
                    reference_ids = line.order_id.stock_reference_ids
                    if not reference_ids:
                        reference_ids = self.env['stock.reference'].create(
                            line._prepare_reference_vals(),
                        )
                        line.order_id.stock_reference_ids = [
                            Command.set(reference_ids.ids),
                        ]

                    values = line._prepare_procurement_values()
                    product_qty = abs(line.qty * pack_line.quantity)
                    procurement_uom = pack_line.product_id.uom_id

                    procurements.append(self.env['stock.rule'].Procurement(
                        pack_line.product_id, product_qty, procurement_uom,
                        line.order_id.partner_id.property_stock_customer,
                        line.name, line.order_id.name, line.order_id.company_id, values,
                    ))
            else:
                # Standard Odoo logic
                reference_ids = line.order_id.stock_reference_ids
                if not reference_ids:
                    reference_ids = self.env['stock.reference'].create(
                        line._prepare_reference_vals(),
                    )
                    line.order_id.stock_reference_ids = [Command.set(reference_ids.ids)]

                values = line._prepare_procurement_values()
                product_qty = line.qty
                procurement_uom = line.product_id.uom_id

                procurements.append(self.env['stock.rule'].Procurement(
                    line.product_id, product_qty, procurement_uom,
                    line.order_id.partner_id.property_stock_customer,
                    line.name, line.order_id.name, line.order_id.company_id, values,
                ))

        if procurements:
            self.env['stock.rule'].run(procurements)

        # Trigger scheduler and picking confirmation (same as base Odoo 19)
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(
                lambda p: p.state not in ['done', 'cancel'],
            )
            if pickings_to_confirm:
                tracked_lines = order.lines.filtered(
                    lambda pol: pol.product_id.tracking != 'none',
                )
                lines_by_tracked_product = groupby(
                    sorted(tracked_lines, key=lambda pol: pol.product_id.id),
                    key=lambda pol: pol.product_id.id,
                )
                pickings_to_confirm.action_confirm()
                for product_id, p_lines in lines_by_tracked_product:
                    p_lines = self.env['pos.order.line'].concat(*p_lines)
                    moves = pickings_to_confirm.move_ids.filtered(
                        lambda m, pid=product_id: m.product_id.id == pid,
                    )
                    moves.move_line_ids.unlink()
                    moves._add_mls_related_to_order(p_lines, are_qties_done=False)
                    moves._recompute_state()
        return True

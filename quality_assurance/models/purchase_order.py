# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models


class PurchaseOrder(models.Model):
    """Extend purchase order to customize picking creation."""
    _inherit = "purchase.order"

    def _create_picking(self):
        """Create or reuse a stock picking and generate stock moves."""
        stock_picking = self.env['stock.picking']

        for order in self:
            if any(ptype == 'consu'
                   for ptype in order.order_line.mapped('product_id.type')):

                pickings = order.picking_ids.filtered(
                    lambda p: p.state not in ('done', 'cancel')
                )

                if not pickings:
                    picking = stock_picking.create(order._prepare_picking())
                else:
                    picking = pickings[0]

                moves = order.order_line._create_stock_moves(picking)
                moves = moves.filtered(
                    lambda m: m.state not in ('done', 'cancel')
                )._action_confirm()

                seq = 0
                for move in sorted(moves, key=lambda m: m.date):
                    seq += 5
                    move.sequence = seq

                moves._action_assign()
                picking.generate_quality_alert()

                self.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': picking, 'origin': order},
                    subtype_xmlid='mail.mt_note',
                )

        return True

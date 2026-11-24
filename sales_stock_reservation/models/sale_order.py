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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    """Inherits sale.order to enable stock reservation for draft quotations."""

    _inherit = "sale.order"

    apply_stock_reservation = fields.Boolean(
        copy=False,
        help="Enable stock reservation for draft quotations.",
    )
    state_reservation = fields.Selection(
        [('reserved', 'Reserved'), ('cancel', 'Cancelled')],
        copy=False,
        help="Current reservation status of the sales quotation.",
    )
    reserved_stock_ids = fields.One2many(
        "stock.reserved",
        "sale_order_id",
        copy=False,
        help="Reserved stock records for this sales quotation.",
    )

    def action_create_stock_reservation(self):
        """Open the stock reservation wizard for storable order lines."""
        self.ensure_one()
        storable_lines = self.order_line.filtered(
            lambda line: line.product_id and line.product_id.is_storable,
        )
        line_vals = [
            (0, 0, {
                'order_line_name': f"{self.name}-{line.name}",
                'product_id': line.product_id.id,
                'quantity': line.product_uom_qty,
                'unit_of_measure_id': line.product_uom_id.id,
                'reserve_quantity': line.product_uom_qty,
            })
            for line in storable_lines
        ] if storable_lines else []
        action = self.env['ir.actions.act_window']._for_xml_id(
            'sales_stock_reservation.sale_stock_reservation_wizard_action',
        )
        action['context'] = {
            'default_sale_order_id': self.id,
            'default_stock_reservation_ids': line_vals,
        }
        return action

    def action_cancel_reservation(self):
        """Cancel stock reservations and cancel related stock moves."""
        self.write({'state_reservation': 'cancel'})
        self.reserved_stock_ids.mapped('move_id')._action_cancel()
        self.reserved_stock_ids.write({'status': 'cancelled'})
        return True

    def action_confirm(self):
        """Confirm the sales order and cancel any active stock reservations."""
        res = super().action_confirm()
        for order in self:
            if order.state_reservation == 'reserved':
                order.action_cancel_reservation()
        return res

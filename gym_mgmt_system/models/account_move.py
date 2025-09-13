# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _activate_gym_memberships(self):
        """Activate gym memberships when invoice is paid"""
        for move in self:
            if move.move_type == "out_invoice" and move.payment_state == "paid":
                sale_order = None

                if move.invoice_origin:
                    sale_order = self.env["sale.order"].search([
                        ("name", "=", move.invoice_origin)
                    ], limit=1)

                if not sale_order:
                    sale_lines = move.invoice_line_ids.mapped('sale_line_ids')
                    if sale_lines:
                        sale_order = sale_lines[0].order_id

                if sale_order:
                    memberships = self.env["gym.membership"].search([
                        ("sale_order_id", "=", sale_order.id),
                        ("state", "=", "confirm")
                    ])

                    for membership in memberships:
                        membership.state = "active"

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def reconcile(self):
        """Check for membership activation after payment reconciliation"""
        res = super().reconcile()

        invoice_moves = self.mapped('move_id').filtered(
            lambda m: m.move_type == 'out_invoice' and m.payment_state == 'paid'
        )

        invoice_moves._activate_gym_memberships()

        return res
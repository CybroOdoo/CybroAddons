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
import logging

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        """Check for membership activation after payment is posted"""
        res = super().action_post()

        for payment in self:
            if payment.partner_type == 'customer' and payment.state == 'posted':
                _logger.info(f"Payment {payment.name} posted, checking for memberships to activate")

                reconciled_invoice_lines = payment.line_ids.mapped(
                    'matched_debit_ids.debit_move_id') + payment.line_ids.mapped('matched_credit_ids.credit_move_id')
                invoices = reconciled_invoice_lines.mapped('move_id').filtered(lambda m: m.move_type == 'out_invoice')

                for invoice in invoices:
                    if invoice.payment_state == 'paid':
                        _logger.info(f"Invoice {invoice.name} is now fully paid")

                        sale_order = None
                        if invoice.invoice_origin:
                            sale_order = self.env["sale.order"].search([
                                ("name", "=", invoice.invoice_origin)
                            ], limit=1)

                        if sale_order:
                            memberships = self.env["gym.membership"].search([
                                ("sale_order_id", "=", sale_order.id),
                                ("state", "=", "confirm")
                            ])

                            for membership in memberships:
                                membership.state = "active"
                                _logger.info(
                                    f"Activated membership {membership.reference} due to payment {payment.name}")
        return res
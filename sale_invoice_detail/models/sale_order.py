# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Deepika V(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models, _


class SaleOrder(models.Model):
    """inherited model sale order for customising """

    _inherit = 'sale.order'

    invoiced_amount = fields.Float("Invoiced Amount",
                                   compute="_compute_invoice_amount",
                                   help="Invoiced Amount for the Order")
    due_amount = fields.Float("Due Amount", help="Due amount in the invoice")
    paid_amount = fields.Float("Paid Amount", help="Paid amount")

    paid_amount_percent = fields.Float("Paid Amount in %",
                                       compute="_compute_paid_amount_percent",
                                       help="Paid amount in percentage")
    payment_count = fields.Integer("Payment Count", help="Payment Count")

    def _compute_invoice_amount(self):
        """Function for computing the invoice amount"""
        for rec in self:
            rec.invoiced_amount = sum(rec.invoice_ids.mapped('amount_total'))
            rec.paid_amount = 0.0
            rec.due_amount = 0.0
            if rec.invoice_ids:
                invoice_names = rec.invoice_ids.mapped('name')
                payments = self.env['account.payment'].search([
                    ('memo', 'in', invoice_names),
                    ('state', '=', 'paid')
                ])
                rec.payment_count = len(payments)
                rec.paid_amount = sum(payments.mapped('amount'))
            rec.due_amount = rec.invoiced_amount - rec.paid_amount

    def _compute_paid_amount_percent(self):
        """function for computing paid amount in percentage"""
        for rec in self:
            rec.paid_amount_percent = 0.0
            if rec.amount_total != 0:
                rec.paid_amount_percent = (rec.paid_amount / rec.amount_total) * 100
            else:
                rec.paid_amount_percent = 0.0

    def action_view_payments(self):
        """action returning to the payments of the order"""
        self.ensure_one()
        if self.invoice_ids:
            invoice_names = [inv.name for inv in self.invoice_ids]
            payment_ids = self.env['account.payment'].search([('memo', 'in', invoice_names)])
            return {
                "type": "ir.actions.act_window",
                "res_model": "account.payment",
                "domain": [('id', 'in', payment_ids.ids)],
                "context": {"create": False},
                "name": _("Customer Payments"),
                'view_mode': 'list,form',
            }

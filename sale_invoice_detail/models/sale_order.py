# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    """Inherited Sale order for viewing the advanced invoice detail"""
    _inherit = 'sale.order'

    invoiced_amount = fields.Float(string="Invoiced Amount",
                                   compute="_compute_invoice_amount",
                                   help="The total amount invoiced")
    due_amount = fields.Float(string="Due Amount",
                              help="The total value invoice that remain unpaid")
    paid_amount = fields.Float(string="Paid Amount",
                               help="The paid amount of the invoice")
    paid_amount_percent = fields.Float(string="Paid Amount in %",
                                       compute="_compute_paid_amount_percent",
                                       help="The percentage of amount paid")

    def _compute_invoice_amount(self):
        """Calculating the invoiced, paid and due amount of the invoice"""
        for invoice in self:
            invoice.invoiced_amount = 0.0
            invoice.paid_amount = 0.0
            invoice.due_amount = 0.0
            if invoice.invoice_ids:
                for inv in self.env['account.move'].search(
                        [('id', 'in', invoice.invoice_ids.ids)]):
                    invoice.invoiced_amount += inv.amount_total
                    invoice.paid_amount += inv.amount_total - inv.amount_residual
                invoice.due_amount = invoice.amount_total - invoice.paid_amount

    def _compute_paid_amount_percent(self):
        """Calculating the percentage of paid amount"""
        for invoice in self:
            invoice.paid_amount_percent = 0.0
            if invoice.invoice_ids:
                p_amount = 0
                for inv in self.env['account.move'].search(
                        [('id', 'in', invoice.invoice_ids.ids)]):
                    p_amount += inv.amount_total - inv.amount_residual
                invoice.paid_amount_percent = (p_amount / invoice.amount_total) * 100

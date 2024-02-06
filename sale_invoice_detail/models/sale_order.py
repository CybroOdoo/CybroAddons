# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anurudh P (odoo@cybrosys.com)
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

    def _compute_invoice_amount(self):
        """ function for computing the invoice amount"""
        for rec in self:
            rec.invoiced_amount = 0.0
            rec.paid_amount = 0.0
            rec.due_amount = 0.0
            if rec.invoice_ids:
                inv = self.env['account.move'].search([
                    ('id', 'in', rec.invoice_ids.ids)])
                for r in inv:
                    rec.invoiced_amount += r.amount_total
                    rec.paid_amount += r.amount_total - r.amount_residual
                rec.due_amount = rec.amount_total - rec.paid_amount

    def _compute_paid_amount_percent(self):
        """function for computing paid amount in percentage"""
        for rec in self:
            rec.paid_amount_percent = 0.0
            if rec.invoice_ids:
                inv = self.env['account.move'].search(
                    [('id', 'in', rec.invoice_ids.ids)])
                p_amount = 0
                for r in inv:
                    p_amount += r.amount_total - r.amount_residual
                rec.paid_amount_percent = (p_amount/rec.amount_total)*100

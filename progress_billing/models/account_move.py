# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    """
        A class that inherits the currently existing model account.move
    """
    _inherit = 'account.move'

    progress_bill_title = fields.Char(string='Progress Billing Title',
                                      help='Give a title for the progress'
                                           ' billing')
    project_id = fields.Many2one('account.analytic.account',
                                 string='Project', copy=False,
                                 help='Corresponding analytic account for the'
                                      ' invoice')
    total_progress_billing = fields.Float(string="Total Progress Billing",
                                          related='project_id.'
                                                  'total_progress_billing',
                                          copy=False, store=True,
                                          help='Total Progress Billing '
                                               'of the corresponding analytic'
                                               ' account')
    invoice_to_date = fields.Float(string="Invoice To Date",
                                   compute='_compute_invoice_to_date',
                                   copy=False,
                                   store=True,
                                   help='The amount invoiced for the analytic'
                                        ' account till this invoice')
    remaining_progress_billing = fields.Float(
        string="Remaining Progress Billing",
        compute='_compute_remaining_progress_billing',
        copy=False, store=True,
        help='The remaining amount to invoice for the analytic account')
    previously_invoice = fields.Float(string="Previously Invoiced",
                                      compute='_compute_previously_invoiced',
                                      copy=False,
                                      store=True,
                                      help='How much amount previously'
                                           ' invoiced')
    previously_invoice_due = fields.Float(string="Previously Invoiced Due",
                                          compute='_compute_previously_invoiced',
                                          copy=False, store=True,
                                          help='How much amount due previously'
                                               ' invoiced')
    current_invoice = fields.Float(string="Current Invoiced",
                                   compute='_compute_current_invoiced',
                                   copy=False,
                                   store=True,
                                   help='Currently how much amount invoiced')
    less_paid_amount = fields.Float(string="Less Paid Amount",
                                    compute='_compute_less_paid_amount',
                                    copy=False,
                                    store=True,
                                    help='The total amount residual')
    total_due = fields.Float(string="Total Due", compute='_compute_total_due',
                             copy=False, store=True, help='The total due')

    @api.depends('project_id', 'amount_total')
    def _compute_invoice_to_date(self):
        """
            Computes invoice to date depending on project_id and amount_total
        """
        for rec in self:
            rec.invoice_to_date = 0
            if rec.project_id:
                invoice = self.search(
                    ['|', ('state', 'in', ['posted']), ('payment_state', 'in', ['paid']),
                     ('move_type', '=', 'out_invoice'),
                     ('partner_id', '=', rec.partner_id.id),
                     ('project_id', '=', rec.project_id.id)])
                for val in invoice:
                    rec.invoice_to_date = rec.invoice_to_date + val.amount_total

    @api.depends('total_progress_billing', 'invoice_to_date')
    def _compute_remaining_progress_billing(self):
        """
            Computes remaining_progress_billing depending on
            total_progress_billing and invoice_to_date
        """
        for rec in self:
            rec.remaining_progress_billing = (rec.total_progress_billing
                                              - rec.invoice_to_date)

    @api.depends('project_id', 'amount_total', 'amount_residual')
    def _compute_previously_invoiced(self):
        """
            Computes previously_invoice and previously_invoice_due depending
            on project_id, amount_total and amount_residual
        """
        for rec in self:
            rec.previously_invoice = 0
            rec.previously_invoice_due = 0
            if rec.project_id:
                invoice = self.search(['|', ('state', 'in', ['posted']),
                                       ('payment_state', 'in', ['paid']),
                                       ('move_type', '=', 'out_invoice'),
                                       ('partner_id', '=', rec.partner_id.id),
                                       ('project_id', '=', rec.project_id.id)])
                if len(invoice) == 1:
                    rec.previously_invoice = 0
                if len(invoice) > 1:
                    rec.previously_invoice = 0
                    for val in invoice:
                        if val.id != rec.id:
                            rec.previously_invoice += val.amount_total
                            rec.previously_invoice_due += val.amount_residual

    @api.depends('amount_total')
    def _compute_current_invoiced(self):
        """
            Computes current_invoice depending on amount_total
        """
        for rec in self:
            rec.current_invoice = rec.amount_total

    @api.depends('amount_residual')
    def _compute_less_paid_amount(self):
        """
            Computes less_paid_amount depending on amount_residual
        """
        for rec in self:
            rec.less_paid_amount = rec.amount_residual

    @api.depends('less_paid_amount', 'previously_invoice', 'current_invoice')
    def _compute_total_due(self):
        """
            Computes total_due depending on less_paid_amount,
            previously_invoice and current_invoice
        """
        for rec in self:
            rec.total_due = rec.previously_invoice_due + rec.less_paid_amount

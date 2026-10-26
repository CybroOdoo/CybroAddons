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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models, Command


class RepaymentLines(models.Model):
    """Loan repayments """
    _name = "repayment.line"
    _description = "Repayment Line"

    name = fields.Char(string="Loan ", default="/", readonly=True,
                       help="Repayment no: of loan")
    partner_id = fields.Many2one('res.partner', string="Partner",
                                 required=True, readonly=True,
                                 help="Partner")
    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True,
                                 help="Company",
                                 default=lambda self: self.env.company)
    date = fields.Date(string="Payment Date", required=True,
                       default=fields.Date.today,
                       readonly=True,
                       help="Date of the payment")
    amount = fields.Float(string="Amount", required=True, help="Amount",
                          digits=(16, 2), readonly=True)
    interest_amount = fields.Float(string="Interest Amount", required=True,
                                   help="Interest Amount", digits=(16, 2), readonly=True)
    total_amount = fields.Float(string="Total Amount", required=True,
                                help="Total Amount", digits=(16, 2), readonly=True)
    loan_id = fields.Many2one('loan.request', string="Loan Ref.",
                              help="Loan", ondelete="restrict",
                              readonly=True)
    state = fields.Selection(string="State",
                             selection=[('unpaid', 'Unpaid'),
                                        ('invoiced', 'Invoiced'),
                                        ('paid', 'Paid')], copy=False,
                             default='unpaid',
                             help="Includes paid and unpaid states for each "
                                  "repayments", )
    journal_loan_id = fields.Many2one('account.journal',
                                      string="Journal",
                                      store=True,
                                      default=lambda self: self.env['account.journal'].search(
                                          [('type', '=', 'bank'), ('company_id', '=', self.env.company.id)],
                                          limit=1
                                      ) or self.env['account.journal'].search(
                                          [('type', '=', 'bank')],
                                          limit=1
                                      ),
                                      help="Journal Record")
    interest_account_id = fields.Many2one('account.account',
                                          string="Interest",
                                          store=True,
                                          help="Account For Interest")
    repayment_account_id = fields.Many2one('account.account',
                                           string="Repayment",
                                           store=True,
                                           help="Account For Repayment")
    invoice = fields.Boolean(string="invoice", default=False,
                             help="For monitoring the record", readonly=True)

    def action_pay_emi(self):
        """Creates invoice for each EMI"""
        self.ensure_one()
        time_now = self.date or fields.Date.today()
        ir_config = self.env['ir.config_parameter'].sudo()
        interest_product_id = ir_config.get_int('advanced_loan_management.interest_product_id') or False
        repayment_product_id = ir_config.get_int('advanced_loan_management.repayment_product_id') or False
        if not repayment_product_id:
            repayment_product = self.env.ref('advanced_loan_management.loan_management_repayment', raise_if_not_found=False)
            repayment_product_id = repayment_product.id if repayment_product else False
        if not interest_product_id:
            interest_product = self.env.ref('advanced_loan_management.loan_management_interest', raise_if_not_found=False)
            interest_product_id = interest_product.id if interest_product else False

        loan_lines_ids = self.env['repayment.line'].search(
            [('loan_id', '=', self.loan_id.id)], order='date asc')
        for line in loan_lines_ids:
            if line.date < self.date and line.state in ('unpaid', 'invoiced'):
                message_id = self.env['message.popup'].create(
                    {'message': "You have pending amounts"})
                return {
                    'name': 'Repayment',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'message.popup',
                    'res_id': message_id.id,
                    'target': 'new'
                }

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': time_now,
            'partner_id': self.partner_id.id,
            'currency_id': self.company_id.currency_id.id,
            'payment_reference': self.name,
            'repayment_line_id': self.id,
            'invoice_line_ids': [
                Command.create({
                    'price_unit': self.amount,
                    'product_id': repayment_product_id,
                    'name': 'Repayment',
                    'account_id': self.repayment_account_id.id if self.repayment_account_id else False,
                    'quantity': 1,
                }),
                Command.create({
                    'price_unit': self.interest_amount,
                    'product_id': interest_product_id,
                    'name': 'Interest amount',
                    'account_id': self.interest_account_id.id if self.interest_account_id else False,
                    'quantity': 1,
                }),
            ],
        })
        if invoice:
            invoice.action_post()
            self.invoice = True
            self.write({'state': 'invoiced'})
        return {
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
        }

    def action_view_invoice(self):
        """To view the invoices"""
        self.ensure_one()
        invoice = self.env['account.move'].search([
            ('repayment_line_id', '=', self.id)
        ], limit=1)
        if not invoice:
            invoice = self.env['account.move'].search([
                ('payment_reference', '=', self.name)
            ], limit=1)
        self.invoice = True

        return {
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id if invoice else False,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
        }

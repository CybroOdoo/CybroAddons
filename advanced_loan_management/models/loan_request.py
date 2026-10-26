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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class LoanRequest(models.Model):
    """Can create new loan requests and manage records"""
    _name = 'loan.request'
    _inherit = ['mail.thread']
    _description = 'Loan Request'

    name = fields.Char(string='Loan Reference', readonly=True,
                       copy=False, help="Sequence number for loan requests",
                       default=lambda self: 'New')
    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True,
                                 help="Company Name",
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, help="Currency",
                                  default=lambda self: self.env.company.currency_id)
    loan_type_id = fields.Many2one('loan.type', string='Loan Type',
                                   required=True, help="Can choose different "
                                                       "loan types suitable")
    loan_amount = fields.Float(string="Loan Amount",
                               help="Total loan amount", related='loan_type_id.loan_amount')
    disbursal_amount = fields.Float(string="Disbursal Amount",
                                    help="Total loan amount "
                                         "available to disburse", related='loan_type_id.disbursal_amount')
    tenure = fields.Integer(string="Tenure",
                            help="Installment period", related='loan_type_id.tenure')
    interest_rate = fields.Float(string="Interest Rate", help="Interest "
                                                              "percentage", related='loan_type_id.interest_rate')
    date = fields.Date(string="Date", default=fields.Date.today,
                       readonly=True, help="Date")
    partner_id = fields.Many2one('res.partner', string="Partner",
                                 required=True,
                                 help="Partner")
    repayment_lines_ids = fields.One2many('repayment.line',
                                          'loan_id',
                                          string="Loan Line", index=True,
                                          help="Repayment lines")
    documents_ids = fields.Many2many('loan.documents',
                                     string="Proofs",
                                     help="Documents as proof")
    img_attachment_ids = fields.Many2many('ir.attachment',
                                          relation="m2m_ir_identity_card_rel",
                                          column1="documents_ids",
                                          string="Images",
                                          help="Image proofs")
    journal_id = fields.Many2one('account.journal',
                                 string="Journal",
                                 help="Journal types",
                                 domain="[('type', '=', 'purchase'),"
                                        "('company_id', '=', company_id)]",
                                 )
    debit_account_id = fields.Many2one('account.account',
                                       string="Debit account",
                                       help="Choose account for "
                                            "disbursement debit")
    credit_account_id = fields.Many2one('account.account',
                                        string="Credit account",
                                        help="Choose account for "
                                             "disbursement credit")
    reject_reason = fields.Text(string="Reason", help="Displays "
                                                      "rejected reason")
    request = fields.Boolean(string="Request",
                             help="For monitoring the record")
    state = fields.Selection(string='State',
                selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'),
                   ('waiting', 'Waiting For Approval'),
                   ('approved', 'Approved'), ('disbursed', 'Disbursed'),
                   ('rejected', 'Rejected'), ('closed', 'Closed')],
        copy=False, tracking=True, default='draft', help="Loan request states")

    @api.model_create_multi
    def create(self, vals_list):
        """Create auto sequence for the loan request records"""
        for vals in vals_list:
            if vals.get('partner_id'):
                loan_count = self.search([
                    ('partner_id', '=', vals['partner_id']),
                    ('state', 'not in', ('draft', 'rejected', 'closed'))
                ])
                if loan_count:
                    raise UserError(_('The partner already has an ongoing loan.'))
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'increment_loan_ref'
                ) or 'New'
        return super().create(vals_list)

    def action_loan_request(self):
        """Changes the state to confirmed and send confirmation mail"""
        self.write({'state': "confirmed"})
        for loan in self:
            partner = loan.partner_id
            loan_no = loan.name
            subject = 'Loan Confirmation'
            message = (f"Dear {partner.name},<br/> This is a confirmation mail "
                       f"for your loan {loan_no}. We have submitted your loan "
                       f"for approval.")
            outgoing_mail = loan.company_id.email
            if partner.email:
                mail_values = {
                    'subject': subject,
                    'email_from': outgoing_mail,
                    'author_id': self.env.user.partner_id.id,
                    'email_to': partner.email,
                    'body_html': message,
                }
                mail = self.env['mail.mail'].sudo().create(mail_values)
                mail.send()

    def action_request_for_loan(self):
        """Change the state to waiting for approval"""
        if self.request:
            self.write({'state': "waiting"})
        else:
            message_id = self.env['message.popup'].create(
                {'message': _("Compute the repayments before requesting")})
            return {
                'name': _('Repayment'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.popup',
                'res_id': message_id.id,
                'target': 'new'
            }

    def action_loan_approved(self):
        """Change to Approved state"""
        self.write({'state': "approved"})

    def action_disburse_loan(self):
        """Disbursing the loan to customer and creating journal
         entry for the disbursement"""
        for loan in self:
            amount = loan.disbursal_amount
            loan_name = loan.partner_id.name
            reference = loan.name
            journal_id = loan.journal_id.id
            debit_account_id = loan.debit_account_id.id
            credit_account_id = loan.credit_account_id.id
            date_now = loan.date
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': date_now,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': date_now,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
            }
            vals = {
                'name': f'DIS / {reference}',
                'narration': reference,
                'ref': reference,
                'journal_id': journal_id,
                'date': date_now,
                'line_ids': [Command.create(debit_vals), Command.create(credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
        self.write({'state': "disbursed"})

    def action_close_loan(self):
        """Closing the loan"""
        for loan in self:
            unpaid_lines = loan.repayment_lines_ids.filtered(lambda l: l.state != 'paid')
            if unpaid_lines:
                message_id = self.env['message.popup'].create(
                    {'message': _("Pending Repayments")})
                return {
                    'name': _('Repayment'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'message.popup',
                    'res_id': message_id.id,
                    'target': 'new'
                }
            loan.write({'state': "closed"})

    def action_loan_rejected(self):
        """You can add reject reasons here"""
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'name': 'Loan Rejection',
                'res_model': 'reject.reason',
                'target': 'new',
                'view_mode': 'form',
                'context': {'default_loan': self.name}
                }

    def action_compute_repayment(self):
        """This automatically creates the installment the partner needs to pay to
        company based on payment start date and the number of installments."""
        for loan in self:
            loan.request = True
            loan.repayment_lines_ids.unlink()
            date_start = (loan.date or fields.Date.today()) + relativedelta(months=1)
            amount = loan.loan_amount / loan.tenure if loan.tenure else loan.loan_amount
            interest = loan.loan_amount * loan.interest_rate
            interest_amount = interest / loan.tenure if loan.tenure else interest
            total_amount = amount + interest_amount
            partner = loan.partner_id

            interest_account = self.env.ref(
                'advanced_loan_management.loan_management_inrst_accounts',
                raise_if_not_found=False
            ) or self.env['account.account'].search(
                [('account_type', '=', 'liability_current'), ('company_ids', 'in', loan.company_id.id)],
                limit=1
            ) or self.env['account.account'].search(
                [('account_type', '=', 'liability_current')],
                limit=1
            )

            repayment_account = self.env.ref(
                'advanced_loan_management.demo_loan_accounts',
                raise_if_not_found=False
            ) or self.env['account.account'].search(
                [('account_type', 'in', ('asset_current', 'asset_cash')), ('company_ids', 'in', loan.company_id.id)],
                limit=1
            ) or self.env['account.account'].search(
                [('account_type', 'in', ('asset_current', 'asset_cash'))],
                limit=1
            )

            repayment_vals = []
            for rand_num in range(1, loan.tenure + 1):
                repayment_vals.append({
                    'name': f"{loan.name}/{rand_num}",
                    'partner_id': partner.id,
                    'date': date_start,
                    'amount': amount,
                    'interest_amount': interest_amount,
                    'total_amount': total_amount,
                    'interest_account_id': interest_account.id if interest_account else False,
                    'repayment_account_id': repayment_account.id if repayment_account else False,
                    'loan_id': loan.id,
                })
                date_start += relativedelta(months=1)
            if repayment_vals:
                self.env['repayment.line'].create(repayment_vals)
        return True


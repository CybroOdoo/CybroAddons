# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api
from odoo.exceptions import except_orm


class HrLoanAcc(models.Model):
    _inherit = 'hr.loan'

    @api.multi
    def action_approve(self):
        """This create account move for request.
            """
        loan_approve = self.env['ir.values'].get_default('account.config.settings', 'loan_approve')
        contract_obj = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
        if not contract_obj:
            raise except_orm('Warning', 'You must Define a contract for employee')
        if not self.loan_lines:
            raise except_orm('Warning', 'You must compute installment before Approved')
        if loan_approve:
            self.write({'state': 'waiting_approval_2'})
        else:
            raise except_orm('Warning', 'Enable the option for loan approval in accounting settings')

    @api.multi
    def action_double_approve(self):
        """This create account move for request in case of double approval.
            """
        if not self.emp_account_id or not self.treasury_account_id or not self.journal_id:
            raise except_orm('Warning', "You must enter employee account & Treasury account and journal to approve ")
        if not self.loan_lines:
            raise except_orm('Warning', 'You must compute Loan Request before Approved')
        timenow = time.strftime('%Y-%m-%d')
        for loan in self:
            amount = loan.loan_amount
            loan_name = loan.employee_id.name
            reference = loan.name
            journal_id = loan.journal_id.id
            debit_account_id = loan.treasury_account_id.id
            credit_account_id = loan.emp_account_id.id
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                'loan_id': loan.id,
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                'loan_id': loan.id,
            }
            vals = {
                'name': 'Loan For' + ' ' + loan_name,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.post()
        self.write({'state': 'approve'})
        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    loan_id = fields.Many2one('hr.loan', string="Loan")


class HrLoanLineAcc(models.Model):
    _inherit = "hr.loan.line"

    @api.one
    def action_paid_amount(self):
        """This create the account move line for payment of each installment.
            """
        timenow = time.strftime('%Y-%m-%d')
        for line in self:
            if line.loan_id.state != 'approve':
                raise except_orm('Warning', "Loan Request must be approved")
            amount = line.amount
            loan_name = line.employee_id.name
            reference = line.loan_id.name
            journal_id = line.loan_id.journal_id.id
            debit_account_id = line.loan_id.emp_account_id.id
            credit_account_id = line.loan_id.treasury_account_id.id
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
                'loan_id': line.loan_id.id,
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
                'loan_id': line.loan_id.id,
            }
            vals = {
                'name': 'Loan For' + ' ' + loan_name,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.post()
        return True


class HrPayslipAcc(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def compute_sheet(self):
        res = super(HrPayslipAcc, self).compute_sheet()
        if len(self.loan_ids) == 0:
            loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.employee_id.id), ('state', '=', 'approve'),
                                                           ('balance_amount', '!=', 0)])
            if loan_count:
                raise except_orm('Error!', 'Please Update the Loans')
            else:
                return res
        else:
            return res

    @api.multi
    def action_payslip_done(self):
        rules = []
        for line in self.loan_ids:
            if line.paid:
                if self.struct_id:
                    for line_id in self.struct_id.rule_ids:
                        rules.append(line_id.code)
                    if self.struct_id.parent_id:
                        for line_ids in self.struct_id.parent_id.rule_ids:
                            rules.append(line_ids.code)
                if 'LO' in rules:
                    line.action_paid_amount()
                else:
                    raise except_orm('Warning', "Add Salary rule for loan in salary structure")
        return super(HrPayslipAcc, self).action_payslip_done()

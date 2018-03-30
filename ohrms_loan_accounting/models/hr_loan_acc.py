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
        if not self.loan_line_ids:
            raise except_orm('Warning', 'You must compute Loan Request before Approved')
        if loan_approve:
            self.write({'state': 'waiting_approval_2'})
        else:
            raise except_orm('Warning', 'Enable the option for loan approval from accounting department')

    @api.multi
    def action_double_approve(self):
        """This create account move for request in case of double approval.
            """
        if not self.emp_account_id or not self.treasury_account_id or not self.journal_id:
            raise except_orm('Warning', "You must enter employee account & Treasury account and journal to approve ")
        if not self.loan_line_ids:
            raise except_orm('Warning', 'You must compute Loan Request before Approved')
        move_obj = self.env['account.move']
        timenow = time.strftime('%Y-%m-%d')
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        for loan in self:
            amount = loan.loan_amount
            loan_name = loan.employee_id.name
            reference = loan.name
            journal_id = loan.journal_id.id
            move = {
                'name': 'Loan For' + ' ' + loan_name,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'state': 'posted',
            }

            debit_account_id = loan.treasury_account_id.id
            credit_account_id = loan.emp_account_id.id
            if debit_account_id:
                debit_line = (0, 0, {
                    'name': loan_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'loan_id': loan.id,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            if credit_account_id:
                credit_line = (0, 0, {
                    'name': loan_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'loan_id': loan.id,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            move.update({'line_ids': line_ids})
            move_id = move_obj.create(move)
            self.move_id = move_id.id
            self.write({'state': 'approve'})
            return self.write({'move_id': move_id.id})


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    loan_id = fields.Many2one('hr.loan', string="Loan")


class HrLoanLineAcc(models.Model):
    _inherit = "hr.loan.line"

    @api.one
    def action_paid_amount(self):
        """This create the account move line for payment of each installment.
            """
        result = super(HrLoanLineAcc, self).action_paid_amount()
        move_obj = self.env['account.move']
        timenow = time.strftime('%Y-%m-%d')
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0

        for line in self:
            if line.loan_id.state != 'approve':
                raise except_orm('Warning', "Loan Request must be approved")
            amount = line.paid_amount
            loan_name = line.employee_id.name
            print "loan_name",loan_name
            reference = line.loan_id.name
            journal_id = line.loan_id.journal_id.id
            move = {
                'name': 'Loan For' + ' ' + loan_name,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'state': 'posted',
            }

            debit_account_id = line.loan_id.emp_account_id.id
            credit_account_id = line.loan_id.treasury_account_id.id

            if debit_account_id:
                debit_line = (0, 0, {
                    'name': loan_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'loan_id': line.loan_id.id,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            if credit_account_id:
                credit_line = (0, 0, {
                    'name': loan_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'loan_id': line.loan_id.id,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            move.update({'line_ids': line_ids})
            move_id = move_obj.create(move)
            return result
        return True


class HrPayslipAcc(models.Model):
    _inherit = 'hr.payslip'

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

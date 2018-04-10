# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.one
    def compute_total_paid(self):
        """This compute the total paid amount of Loan.
            """
        total = 0.0
        for line in self.loan_ids:
            if line.paid:
                total += line.amount
        self.total_paid = total

    loan_ids = fields.One2many('hr.loan.line', 'payslip_id', string="Loans")
    total_paid = fields.Float(string="Total Loan Amount", compute='compute_total_paid')

    @api.multi
    def get_loan(self):
        """This gives the installment lines of an employee where the state is not in paid.
            """
        loan_list = []
        loan_ids = self.env['hr.loan.line'].search([('employee_id', '=', self.employee_id.id), ('paid', '=', False)])
        for loan in loan_ids:
            if loan.loan_id.state == 'approve':
                loan_list.append(loan.id)
        self.loan_ids = loan_list
        return loan_list

    @api.multi
    def action_payslip_done(self):
        loan_list = []
        for line in self.loan_ids:
            if line.paid:
                loan_list.append(line.id)
            else:
                line.payslip_id = False
        self.loan_ids = loan_list
        return super(HrPayslip, self).action_payslip_done()

# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.one
    def compute_total_paid_loan(self):
        """This compute the total paid amount of Loan.
            """
        total = 0.00
        for line in self.loan_ids:
            if line.paid:
                total += line.paid_amount
        self.total_amount_paid = total

    loan_ids = fields.One2many('hr.loan.line', 'payroll_id', string="Loans")
    total_amount_paid = fields.Float(string="Total Loan Amount", compute='compute_total_paid_loan')

    @api.multi
    def get_loan(self):
        """This gives the installment lines of an employee where the state is not in paid.
            """
        array = []
        loan_ids = self.env['hr.loan.line'].search([('employee_id', '=', self.employee_id.id), ('paid', '=', False)])
        for loan in loan_ids:
            if loan.loan_id.state == 'approve':
                array.append(loan.id)
        self.loan_ids = array
        return array

    @api.multi
    def action_payslip_done(self):
        array = []
        for line in self.loan_ids:
            if line.paid:
                array.append(line.id)
            else:
                line.payroll_id = False
        self.loan_ids = array
        return super(HrPayslip, self).action_payslip_done()

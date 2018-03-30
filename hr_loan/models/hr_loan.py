# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "HR Loan Request"

    @api.one
    def _compute_amount(self):
        total_paid_amount = 0.00
        for loan in self:
            for line in loan.loan_line_ids:
                if line.paid:
                    total_paid_amount += line.paid_amount
            balance_amount = loan.loan_amount - total_paid_amount
            self.total_amount = loan.loan_amount
            self.balance_amount = balance_amount
            self.total_paid_amount = total_paid_amount

    @api.one
    def _get_old_loan(self):
        """This compute employees old loans due amount.
            """
        old_amount = 0.00
        for loan in self.search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approve')]):
            if loan.id != self.id:
                old_amount += loan.balance_amount
        self.loan_old_amount = old_amount

    name = fields.Char(string="Loan Name", default="/", readonly=True)
    date = fields.Date(string="Date Request", default=fields.Date.today(), readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    parent_id = fields.Many2one('hr.employee', related="employee_id.parent_id", string="Manager")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department")
    job_id = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    emp_salary = fields.Float(string="Employee Salary", related="employee_id.contract_id.wage", readonly=True)
    loan_old_amount = fields.Float(string="Old Loan Amount Not Paid", compute='_get_old_loan')
    loan_amount = fields.Float(string="Loan Amount", required=True)
    total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_amount')
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_amount')
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_amount')
    installment = fields.Integer(string="No Of Installments", default=1)
    payment_start_date = fields.Date(string="Start Date of Payment", required=True, default=fields.Date.today())
    loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    move_id = fields.Many2one('account.move', string="Entry Journal", readonly=True)
    emp_account_id = fields.Many2one('account.account', string="Employee Loan Account")
    treasury_account_id = fields.Many2one('account.account', string="Treasury Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Waiting Approval From Hr'),
        ('waiting_approval_2', 'Waiting Approval From Accounts'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.loan.req') or ' '
        res = super(HrLoan, self).create(values)
        return res

    @api.multi
    def action_refuse(self):
        return self.write({'state': 'refuse'})

    @api.multi
    def action_set_to_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def submit(self):
        self.write({'state': 'waiting_approval_1'})

    @api.multi
    def onchange_employee_id(self, employee_id=False):
        old_amount = 0.00
        if employee_id:
            for loan in self.search([('employee_id', '=', employee_id), ('state', '=', 'approve')]):
                if loan.id != self.id:
                    old_amount += loan.balance_amount
            return {
                'value': {
                    'loan_old_amount': old_amount}
            }

    @api.multi
    def action_approve(self):
        self.write({'state': 'approve'})

    @api.multi
    def compute_loan_line(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        loan_line = self.env['hr.loan.line']
        loan_line.search([('loan_id', '=', self.id)]).unlink()
        for loan in self:
            date_start_str = datetime.strptime(loan.payment_start_date, '%Y-%m-%d')
            counter = 1
            amount_per_time = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                line_id = loan_line.create({
                    'paid_date': date_start_str,
                    'paid_amount': amount_per_time,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                counter += 1
                date_start_str = date_start_str + relativedelta(months=1)

        return True

    @api.multi
    def button_reset_balance_total(self):
        """This function recompute the balance.
            """
        total_paid_amount = 0.00
        for loan in self:
            for line in loan.loan_line_ids:
                if line.paid:
                    total_paid_amount += line.paid_amount
            balance_amount = loan.loan_amount - total_paid_amount
            self.write({'total_paid_amount': total_paid_amount, 'balance_amount': balance_amount})


class HrLoanLine(models.Model):
    _name = "hr.loan.line"
    _description = "HR Loan Request Line"

    paid_date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    paid_amount = fields.Float(string="Paid Amount", required=True)
    paid = fields.Boolean(string="Paid")
    notes = fields.Text(string="Notes")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", ondelete='cascade')
    payroll_id = fields.Many2one('hr.payslip', string="Payslip Ref.")

    @api.one
    def action_paid_amount(self):
        return self.write({'paid': True})


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.one
    def _compute_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        count = 0
        loan_remain_amount = 0.00
        loan_ids = self.env['hr.loan'].search([('employee_id', '=', self.id)])
        for loan in loan_ids:
            loan_remain_amount += loan.balance_amount
            count += 1
        self.loan_count = count
        self.loan_amount = loan_remain_amount

    loan_amount = fields.Float(string="loan Amount", compute='_compute_loans')
    loan_count = fields.Integer(string="Loan Count", compute='_compute_loans')



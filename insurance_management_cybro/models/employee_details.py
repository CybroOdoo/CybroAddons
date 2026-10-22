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
import re

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

SALARY_GROUP = 'insurance_management_cybro.group_insurance_manager'


class EmployeeDetails(models.Model):
    """Insurance agents and their salary or commission payments."""
    _name = 'employee.details'
    _description = "Employee Details"
    _check_company_auto = True

    name = fields.Char(required=True, help="Name of the employee")
    company_id = fields.Many2one(
        'res.company', required=True, index=True,
        default=lambda self: self.env.company,
        help="Company this agent works for")
    user_id = fields.Many2one('res.users',
                              string='Related User of the employee',
                              copy=False, help="Related user of the employee")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'),
                               ('others', 'Others')],
                              help="Select the gender of the employee")
    phone = fields.Char(string='Phone Number', required=True,
                        help="Phone number of employee")
    salary_type = fields.Selection(
        [('fixed', 'Fixed'), ('commission', 'Commission'), ('both', 'Both')],
        default='fixed', required=True, groups=SALARY_GROUP,
        help="Select the salary type")
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.company.currency_id,
        help="Currency of the salary")
    base_salary = fields.Monetary(groups=SALARY_GROUP,
                                  help="Base salary of the employee")
    last_salary_date = fields.Date(string='Last Payment On', copy=False,
                                   groups=SALARY_GROUP,
                                   help="Last salary paid date")
    previous_salary_date = fields.Date(
        copy=False, readonly=True, groups=SALARY_GROUP,
        help="Payment date preceding the last payment, used when the last "
             "payment bill is cancelled")
    insurance_ids = fields.One2many('insurance.details',
                                    'employee_id', readonly=True,
                                    string='Insurances',
                                    help="Insurances handled by the agent")
    note_field = fields.Html(string='Comment', help="Give notes, if any")
    invoice_id = fields.Many2one('account.move',
                                 string='Last payment', readonly=True,
                                 copy=False, groups=SALARY_GROUP,
                                 help="Bill of the last payment")

    def _get_commission(self, date_from, date_to):
        """Return the commission earned on the confirmed or closed
        insurances started after `date_from` and up to `date_to`."""
        self.ensure_one()
        commission = 0.0
        for insurance in self.insurance_ids:
            if insurance.state not in ('confirmed', 'closed'):
                continue
            if insurance.start_date > date_to or (
                    date_from and insurance.start_date <= date_from):
                continue
            amount = insurance.currency_id._convert(
                insurance.amount, self.currency_id, self.company_id,
                insurance.start_date)
            commission += insurance.commission_rate / 100.0 * amount
        return commission

    def action_salary_payment(self):
        """Create the vendor bill paying the agent salary and/or the
        commission earned since the last payment."""
        self.ensure_one()
        self.env['account.move'].check_access('create')
        if not self.user_id:
            raise UserError(self.env._(
                "Set the related user of the agent to pay the salary."))
        last_bill = self.invoice_id
        if last_bill.state == 'draft':
            raise UserError(self.env._(
                "You must validate the last payment made in "
                "order to create a new payment"))
        # A cancelled bill never paid its period, so pay from the date
        # preceding it.
        if last_bill.state == 'cancel':
            since = self.previous_salary_date
        else:
            since = self.last_salary_date
        today = fields.Date.context_today(self)
        if since and since >= today:
            raise UserError(self.env._(
                "The salary has already been paid on %(date)s.",
                date=since))

        commission = self._get_commission(since, today)
        if self.salary_type == 'fixed':
            amount = self.base_salary
        elif self.salary_type == 'commission':
            amount = commission
        else:
            amount = self.base_salary + commission
        amount = self.currency_id.round(amount)
        if amount <= 0.0:
            raise UserError(self.env._("Amount should be greater than zero"))

        bill = self.env['account.move'].with_company(self.company_id).create({
            'move_type': 'in_invoice',
            'invoice_date': today,
            'partner_id': self.user_id.partner_id.id,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.env.user.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [fields.Command.create({
                'name': self.env._(
                    "Salary payment for %(agent)s", agent=self.name),
                'quantity': 1,
                'price_unit': amount,
            })],
        })
        self.write({
            'invoice_id': bill.id,
            'previous_salary_date': since,
            'last_salary_date': today,
        })
        return bill._get_records_action()

    @api.constrains('phone')
    def _check_phone(self):
        """Allow an optional leading +, digits, spaces and hyphens."""
        for rec in self:
            if rec.phone and not re.fullmatch(
                    r'\+?\d[\d \-]{5,18}\d', rec.phone):
                raise ValidationError(self.env._(
                    "Enter a valid phone number: 7 to 20 digits, with an "
                    "optional leading + and spaces or hyphens."))

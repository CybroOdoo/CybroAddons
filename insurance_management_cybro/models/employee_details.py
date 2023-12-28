# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen @cybrosys(odoo@cybrosys.com)
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
#############################################################################
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class EmployeeDetails(models.Model):
    """This class creates a model 'employee.details' and added fields """
    _name = 'employee.details'
    _description = "Employee Details"

    name = fields.Char(string='Name', required=True,
                       help="Name of the employee")
    user_id = fields.Many2one(
        'res.users', string='Related User', copy=False,
        help="Related user")
    sex = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('others', 'Others')],
        help="Select the sex of the employee")
    phone = fields.Char(string='Phone Number', help="Phone number of employee",
                        required=True)
    salary_type = fields.Selection(
        [('fixed', 'Fixed'), ('commission', 'Commission'), ('both', 'Both')],
        default='fixed', required=True, help="Select the salary type")
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
        help="Select the currency")
    base_salary = fields.Monetary(string='Base Salary',
                                  help="Give the base salary of employee")
    last_salary_date = fields.Date(string='Last Payment On', copy=False,
                                   help="Last salary paid date")
    insurance_ids = fields.One2many('insurance.details',
                                    'employee_id',
                                    string='Last Details', readonly=True,
                                    help="Insurance details created "
                                         "by employee")
    note_field = fields.Html(string='Comment',
                             help="Give notes,if any")
    invoice_id = fields.Many2one(
        'account.move', string='Last payment', copy=False,
        readonly=True,
        help="Invoice of last payment")

    def action_salary_payment(self):
        """This function raises a user error if state is draft and
        user error when base salary is less
        and creates invoice with corresponding details given"""
        if self.invoice_id:
            if self.invoice_id.state == 'draft':
                raise UserError(_("You must validate the last payment made in "
                                  "order to create a new payment"))
        amount = 0.0
        if self.salary_type == 'fixed':
            amount = self.base_salary
            if self.base_salary == 0.0:
                raise UserError(_("Amount should be greater than zero"))
        elif self.salary_type == 'commission':
            for ins in self.insurance_ids:
                if self.last_salary_date:
                    if ins.start_date > self.last_salary_date:
                        amount += (ins.commission_rate * ins.amount) / 100
        else:
            for ins in self.insurance_ids:
                if self.last_salary_date:
                    if ins.start_date > self.last_salary_date:
                        amount += ((ins.commission_rate * ins.amount) / 100 +
                                   self.base_salary)
        invoice_date = self.env['account.move'].sudo().create({
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.context_today(self),
            'partner_id': self.user_id.partner_id.id,
            'invoice_user_id': self.env.user.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [(fields.Command.create({
                'name': 'Invoice For Salary Payment',
                'quantity': 1,
                'price_unit': amount,
                'account_id': 41,
            }))],
        })
        self.sudo().write({
            'invoice_id': invoice_date.id,
            'last_salary_date': fields.Date.context_today(self),
        })

    @api.constrains('phone')
    def check_phone(self):
        """ Make sure phone contains only 10 digits """
        for rec in self:
            if not re.match('^[0-9]{10}$', rec.phone):
                raise ValidationError(
                    _('Phone number should contain exactly 10 digits and only '
                      'numbers are allowed'))

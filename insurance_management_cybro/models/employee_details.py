# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EmployeeDetails(models.Model):
    _name = 'employee.details'

    name = fields.Char(string='Name', required=True)
    related_partner = fields.Many2one('res.users', string='Related User', copy=False)
    sex = fields.Selection([('male', 'Male'), ('female', 'Female')])
    phone = fields.Float(string='Phone Number', size=15, digits=(15, 0))
    salary_type = fields.Selection([('fixed', 'Fixed'), ('commission', 'Commission'), ('both', 'Both')],
                                   default='commission', required=True)
    base_salary = fields.Integer(string='Base Salary')
    last_salary = fields.Datetime(string='Last Payment On', copy=False)
    insurance_ids = fields.One2many('insurance.details', 'employee_id', string='Last Payment On', readonly=True)
    note_field = fields.Html(string='Comment')
    invoice_id = fields.Many2one('account.invoice', string='Last payment', copy=False, readonly=True)

    @api.multi
    def salary_payment(self):
        if self.invoice_id:
            if self.invoice_id.state == 'draft':
                raise UserError(_("You Must validate last payment made in order to create a new payment"))
        amount = 0
        if self.salary_type == 'fixed':
            amount = self.base_salary
        elif self.salary_type == 'commission':
            for ins in self.insurance_ids:
                if self.last_salary:
                    if ins.date_start > self.last_salary:
                        amount += (ins.commission_rate * ins.amount)/100
        else:
            amount = self.base_salary
            for ins in self.insurance_ids:
                if ins.date_start > self.last_salary:
                    amount += (ins.commission_rate * ins.amount) / 100

        if amount == 0:
            raise UserError(_("Amount should be greater than zero"))
        invoice_date = self.env['account.invoice'].create({
            'type': 'in_invoice',
            'partner_id': self.related_partner.partner_id.id,
            'user_id': self.env.user.id,
            'claim_id': self.id,
            'origin': self.name,
            'invoice_line_ids': [(0, 0, {
                'name': 'Invoice For Insurance Claim',
                'quantity': 1,
                'price_unit': amount,
                'account_id': 41,
            })],
        })
        self.invoice_id = invoice_date.id
        self.last_salary = fields.Date.today()

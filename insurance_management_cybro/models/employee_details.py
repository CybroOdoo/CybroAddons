# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
    _name = 'employee.details'

    name = fields.Char(string='Name', required=True)
    user_id = fields.Many2one(
        'res.users', string='Related User', copy=False)
    sex = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('others', 'Others')])
    phone = fields.Char(string='Phone Number')
    salary_type = fields.Selection(
        [('fixed', 'Fixed'), ('commission', 'Commission'), ('both', 'Both')],
        default='commission', required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    base_salary = fields.Monetary(string='Base Salary')
    last_salary_date = fields.Date(string='Last Payment On', copy=False)
    insurance_ids = fields.One2many('insurance.details', 'employee_id',
                                    string='Last Payment On', readonly=True)
    note_field = fields.Html(string='Comment')
    invoice_id = fields.Many2one(
        'account.move', string='Last payment', copy=False, readonly=True)

    def action_salary_payment(self):
        if self.invoice_id:
            if self.invoice_id.state == 'draft':
                raise UserError(_("You must validate the last payment made in "
                                  "order to create a new payment"))
        amount = 0.0
        if self.base_salary == 0.0:
            raise UserError(_("Amount should be greater than zero"))
        if self.salary_type == 'fixed':
            amount = self.base_salary
        elif self.salary_type == 'commission':
            for ins in self.insurance_ids:
                if self.last_salary_date:
                    if ins.start_date > self.last_salary_date:
                        amount += (ins.commission_rate * ins.amount) / 100
        else:
            amount = self.base_salary
            for ins in self.insurance_ids:
                if ins.start_date > self.last_salary_date:
                    amount += (ins.commission_rate * ins.amount) / 100
        invoice_date = self.env['account.move'].sudo().create({
            'move_type': 'in_invoice',
            'invoice_date': fields.Date.context_today(self),
            'partner_id': self.user_id.partner_id.id,
            'invoice_user_id': self.env.user.id,
            'claim_id': self.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [(0, 0, {
                'name': 'Invoice For Insurance Claim',
                'quantity': 1,
                'price_unit': amount,
                'account_id': 41,
            })],
        })
        self.sudo().write({
            'invoice_id': invoice_date.id,
            'last_salary_date': fields.Date.context_today(self),
        })

    @api.constrains('phone')
    def check_phone(self):
        """ make sure phone contains only numbers"""
        for rec in self:
            if not re.match('^[0-9]*$', rec.phone):
                raise ValidationError(
                    _('Only numbers are permitted in phone number'))

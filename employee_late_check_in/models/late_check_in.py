# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Ijaz Ahammed (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, fields, api


class LateCheckIn(models.Model):
    _name = 'late.check_in'

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee', string="Employee")
    late_minutes = fields.Integer(string="Late Minutes")
    date = fields.Date(string="Date")
    amount = fields.Float(string="Amount", compute="get_penalty_amount")
    state = fields.Selection([('draft', 'Draft'),
                              ('approved', 'Approved'),
                              ('refused', 'Refused'),
                              ('deducted', 'Deducted')], string="state",
                             default="draft")
    attendance_id = fields.Many2one('hr.attendance', string='attendance')

    # current_user_boolean = fields.Boolean()
    @api.model
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('late.check_in') or '/'
        values['name'] = seq
        return super(LateCheckIn, self.sudo()).create(values)

    def get_penalty_amount(self):
        for rec in self:
            amount = float(self.env['ir.config_parameter'].sudo().get_param('deduction_amount'))
            rec.amount = amount
            if self.env['ir.config_parameter'].sudo().get_param('deduction_type') == 'minutes':
                rec.amount = amount * rec.late_minutes

    def approve(self):
        self.state = 'approved'

    def reject(self):
        self.state = 'refused'

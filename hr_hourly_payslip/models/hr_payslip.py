# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Busthana Shirin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime, time
from odoo import api, fields, models


class HrPayslip(models.Model):
    """ Class for the inherited model hr_payslip """
    _inherit = 'hr.payslip'

    total_hours = fields.Float(
        compute='_compute_total_hours',
        store=True,
        digits=(16, 4),
        help='Total worked hours of the employee in the selected period.',
    )
    hour_based_salary = fields.Float(
        compute='_compute_hour_based_salary',
        store=True,
        help='Salary based on the worked hours for the employee.',
    )
    show_total_hours = fields.Boolean(
        compute='_compute_show_total_hours',
        store=True,
        help='Shows the total hours in the view only if Hourly Payslip is'
             ' enabled in the employee profile.',
    )

    @api.depends('employee_id', 'employee_id.hourly_payslip')
    def _compute_show_total_hours(self):
        """ Compute whether to show the Total Hours field based on whether
        the hourly payslip option is enabled for the employee. """
        for record in self:
            record.show_total_hours = bool(
                record.employee_id and record.employee_id.hourly_payslip
            )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """ This function helps to show the Total Hours field if the hourly
        payslip is available for the employee. """
        parent_onchange = getattr(super(), '_onchange_employee_id', None)
        res = parent_onchange() if callable(parent_onchange) else None
        if self.employee_id and self.employee_id.hourly_payslip:
            self.show_total_hours = True
        else:
            self.show_total_hours = False
        return res

    @api.depends('date_from', 'date_to', 'employee_id',
                 'employee_id.attendance_ids.check_in',
                 'employee_id.attendance_ids.worked_hours')
    def _compute_total_hours(self):
        """ Function to compute total worked hours to the particular employee
        for the given period of date. """
        for record in self:
            if (not record.employee_id
                    or not record.date_from
                    or not record.date_to):
                record.total_hours = 0.0
                continue
            dt_from = datetime.combine(record.date_from, time.min)
            dt_to = datetime.combine(record.date_to, time.max)
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', record.employee_id.id),
                ('check_in', '>=', fields.Datetime.to_string(dt_from)),
                ('check_in', '<=', fields.Datetime.to_string(dt_to)),
            ])
            record.total_hours = sum(attendances.mapped('worked_hours'))

    @api.depends('total_hours', 'employee_id', 'employee_id.hourly_cost')
    def _compute_hour_based_salary(self):
        """ Function to compute salary based on the worked hours for the
        employee. """
        for record in self:
            if not record.employee_id:
                record.hour_based_salary = 0.0
                continue
            record.hour_based_salary = (
                record.employee_id.hourly_cost * record.total_hours
            )

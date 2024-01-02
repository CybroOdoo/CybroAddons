# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(odoo@cybrosys.com)
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
from odoo import models, fields, api


class HrPayroll(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Employee Payroll'

    payslip_state = fields.Char(compute="compute_payslip_state", store=True)

    @api.depends('state')
    def compute_payslip_state(self):
        """Compute the label value of the payslip state"""
        for rec in self:
            rec.payslip_state = dict(self._fields[
                                            'state'].selection).get(rec.state)

    @api.model
    def get_employee_payslips(self):
        """return employee payslip details"""
        self._cr.execute(
            """SELECT hr_payslip.payslip_state,count(*) FROM hr_employee 
            JOIN hr_payslip ON hr_payslip.employee_id=hr_employee.id 
            GROUP BY hr_payslip.payslip_state
            """)
        dat = self._cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            if dat[i][0] is not None:
                data.append({'label': dat[i][0], 'value': dat[i][1]})
        return data


class HrLeave(models.Model):
    _inherit = 'hr.leave'
    state_string = fields.Char(compute="compute_state_string", store=True)

    @api.depends('state')
    def compute_state_string(self):
        """Compute the label of the leave state"""
        for rec in self:
            rec.state_string = dict(self._fields[
                                           'state'].selection).get(rec.state)

    @api.model
    def get_employee_time_off(self):
        """return employee time off details"""
        self._cr.execute("""SELECT hr_leave.state_string, count(*) 
        FROM hr_employee JOIN hr_leave ON hr_leave.employee_id=hr_employee.id 
        GROUP BY hr_leave.state_string""")
        dat = self._cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})
        return data

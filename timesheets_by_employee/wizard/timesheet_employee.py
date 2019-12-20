# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Kavya Raveendran (odoo@cybrosys.com)
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields


class EmployeeTimesheet(models.TransientModel):
    _name = 'timesheet.wizard'

    employee = fields.Many2one('res.users', string="Employee", required=True)
    from_date = fields.Date(string="Starting Date")
    to_date = fields.Date(string="Ending Date")

    def print_timesheet(self):
        """Redirects to the report with the values obtained from the wizard
        'data['form']': name of employee and the date duration"""
        data = {
            'start_date': self.from_date,
            'end_date': self.to_date,
            'employee': self.employee.id
        }
        return self.env.ref('timesheets_by_employee.action_report_print_timesheets').report_action(self, data=data)


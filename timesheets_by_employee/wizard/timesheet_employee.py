# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
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

from openerp import models, fields, api


class EmployeeTimesheet(models.TransientModel):
    _name = 'timesheet.wizard'

    employee = fields.Many2one('hr.employee', string="Employee", required=True)
    from_date = fields.Date(string="Starting Date")
    to_date = fields.Date(string="Ending Date")

    @api.model
    def print_timesheet(self, data):
        """Redirects to the report with the values obtained from the wizard
                'data['form']': name of employee and the date duration"""
        rec = self.browse(data)
        data = {}
        data['form'] = rec.read(['employee', 'from_date', 'to_date'])
        return self.env['report'].get_action(self.browse(data), 'timesheets_by_employee.report_timesheets', data=data)


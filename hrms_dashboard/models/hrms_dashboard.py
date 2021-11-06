# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Aswani PC, Saritha Sahadevan (<https://www.cybrosys.com>)
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
from odoo import models, api, _
from odoo.http import request


class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_user_employee_details(self):
        uid = request.session.uid
        employee = self.env['hr.employee'].sudo().search_read([('user_id', '=', uid)], limit=1)
        leaves_to_approve = self.env['hr.holidays'].sudo().search_count([('state', 'in', ['confirm', 'validate1']),
                                                                         ('type', '=', 'remove')])
        leaves_alloc_req = self.env['hr.holidays'].sudo().search_count([('state', 'in', ['confirm', 'validate1'])
                                                                                  , ('type', '=', 'add')])
        timesheets_to_approve = self.env['hr_timesheet_sheet.sheet'].sudo().search_count(
            [('state', 'in', ['confirm'])])
        job_applications = self.env['hr.applicant'].sudo().search_count([])
        if employee:
            data = {
                'leaves_to_approve': leaves_to_approve,
                'leaves_alloc_req': leaves_alloc_req,
                'timesheets_to_approve': timesheets_to_approve,
                'job_applications': job_applications,
            }
            employee[0].update(data)
        return employee

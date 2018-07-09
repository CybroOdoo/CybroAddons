# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
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
from dateutil.relativedelta import relativedelta
from odoo.report import report_sxw
from odoo.osv import osv
from odoo import fields
from odoo.http import request


class EmployeeWorkloadReportCommon(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(EmployeeWorkloadReportCommon, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_mxm_workload': self.get_mxm_workload,
            'get_line': self.get_lines,
        })
        self.context = context

    def get_mxm_workload(self, data):
        start_date = fields.Date.from_string(data['form']['from_date'])
        end_date = fields.Date.from_string(data['form']['to_date'])
        no_of_days = relativedelta(end_date, start_date)
        maximum_workload = data['form']['working_hr'] * no_of_days.days
        return maximum_workload

    def get_lines(self, data):
        obj = request.env['res.users'].search([])
        lines = []
        for each in obj:
            workload_hrs = 0.0
            workload_perc = 0.0
            obj1 = request.env['project.task'].search([('user_id', '=', each.id),
                                                       ('date_deadline', '>=', data['form']['from_date']),
                                                       ('date_deadline', '<=', data['form']['to_date'])])
            for each1 in obj1:
                time_now = fields.Date.from_string(fields.Date.today())
                deadline = fields.Date.from_string(each1.date_deadline)
                workload = relativedelta(deadline, time_now)
                workload_hrs = workload_hrs + workload.days
            maximum_workload = self.get_mxm_workload(data)
            workload_perc = (workload_hrs / maximum_workload) * 100
            if workload_perc > 100:
                status = 'Over Workload'
            elif workload_perc > 75:
                status = 'Busy'
            elif workload_perc > 50:
                status = 'Normal'
            elif workload_perc > 0:
                status = 'Less Workload'
            else:
                status = 'Free'
            vals = {
                'employee': each.name,
                'no_of_works': len(obj1),
                'workload': workload_hrs,
                'workload_perc': workload_perc,
                'status': status,
            }
            lines.append(vals)
        return lines


class PrintReport(osv.AbstractModel):
    _name = 'report.workload_in_project.report_employee_workload'
    _inherit = 'report.abstract_report'
    _template = 'workload_in_project.report_employee_workload'
    _wrapped_report_class = EmployeeWorkloadReportCommon


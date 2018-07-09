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
from datetime import datetime, timedelta
from odoo import models, fields, api, _


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    progress_rate = fields.Integer(string='Workload')
    maximum_rate = fields.Integer()

    @api.model
    def fields_view_get(self, view_id=None, view_type='kanban', toolbar=False, submenu=False):
        ret_val = super(ResUsersInherit, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        for each in self.search([]):
            workload_hrs = 0.0
            workload_perc = 0.0
            ir_values = self.env['ir.values']
            no_of_days = ir_values.get_default('project.config.settings', 'no_of_days')
            no_of_hrs = ir_values.get_default('project.config.settings', 'working_hr')
            if no_of_days:
                to_date = datetime.today() + timedelta(days=no_of_days)
            else:
                to_date = datetime.today() + timedelta(days=6)
            obj1 = self.env['project.task'].search([('user_id', '=', each.id),
                                                    ('date_deadline', '>=', fields.Date.today()),
                                                    ('date_deadline', '<=', to_date)])
            for each1 in obj1:
                time_now = fields.Date.from_string(fields.Date.today())
                deadline = fields.Date.from_string(each1.date_deadline)
                workload = relativedelta(deadline, time_now)
                workload_hrs = workload_hrs + workload.days
            start_date = fields.Date.from_string(fields.Date.today())
            end_date1 = to_date.strftime('%Y-%m-%d')
            end_date = fields.Date.from_string(end_date1)
            no_of_days1 = relativedelta(end_date, start_date)
            if no_of_hrs:
                maximum_workload = no_of_hrs * no_of_days1.days
            else:
                maximum_workload = 8 * no_of_days1.days
            workload_perc = (workload_hrs / maximum_workload) * 100
            each.write({'maximum_rate': 100,
                        'progress_rate': workload_perc})
        return ret_val


class ProjectSettings(models.TransientModel):
    _inherit = 'project.config.settings'

    working_hr = fields.Integer(string='Working Hr/day', default=8)
    no_of_days = fields.Integer(string='No of days for calculation', default=6)
    block_busy_users = fields.Boolean(string='Block busy users ?', default=False)

    @api.multi
    def set_block_busy_users(self):
        return self.env['ir.values'].sudo().set_default(
            'project.config.settings', 'block_busy_users', self.block_busy_users)

    @api.multi
    def set_working_hr(self):
        return self.env['ir.values'].sudo().set_default(
            'project.config.settings', 'working_hr', self.working_hr)

    @api.multi
    def set_no_of_days(self):
        return self.env['ir.values'].sudo().set_default(
            'project.config.settings', 'no_of_days', self.no_of_days)


class ProjectInherit(models.Model):
    _inherit = 'project.task'

    @api.constrains('user_id')
    def validation(self):
        ir_values = self.env['ir.values']
        block_users = ir_values.get_default('project.config.settings', 'block_busy_users')
        if block_users:
            if self.user_id.progress_rate > 80:
                raise Warning(_('%s is %s percentage Overloaded with Work') % (self.user_id.name, self.user_id.progress_rate))


class EmployeeWorkloadReport(models.TransientModel):
    _name = "wizard.workload.report"
    _description = "Employee Workload Report"

    working_hr = fields.Integer(string='Working Hr/day', required=True, default=8)
    from_date = fields.Date(string='From Date', required=True, default=lambda *a: datetime.now().strftime('%Y-%m-%d'))
    to_date = fields.Date(string='To Date', required=True, default=datetime.today() + timedelta(days=6))

    @api.multi
    def workload_report(self):
        data = self.read()[0]
        datas = {
            'ids': [],
            'model': 'wizard.workload.report',
            'form': data
        }
        return self.env['report'].get_action(self, 'workload_in_project.report_employee_workload', data=datas)


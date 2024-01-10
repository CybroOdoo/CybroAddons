# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
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
###############################################################################
from ast import literal_eval
from datetime import datetime
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    """This model inherit Account analytic line."""
    _inherit = 'account.analytic.line'

    status = fields.Selection([('ongoing', 'Ongoing'),
                               ('completed', 'Completed')], string='Status',
                              default='ongoing', help='Status of task.')

    def write(self, values):
        """Generate work report on creating new record."""
        work_report = self.env['ir.config_parameter'].sudo().get_param(
            'work_report_from_timesheet.report_method')
        if work_report == 'task_report':
            self._send_daily_task_report()
        result = super().write(values)
        return result

    def _send_daily_task_report(self):
        """Work report for each task will be generated and sent to the
        employee that chosen in timesheet settings."""
        params = self.env['ir.config_parameter'].sudo()
        manager_email = params.get_param(
            'work_report_from_timesheet.employee_id')
        cc_employees = literal_eval(
            params.get_param('work_report_from_timesheet.employee_ids'))
        template_id = self.env.ref('work_report_from_timesheet.'
                                   'email_template_work_report_from_timesheet')
        for rec in self:
            email_vals = {
                'message_type': 'notification',
                'is_notification': True,
                'email_to': self.env['hr.employee'].browse(
                    int(manager_email)).work_email,
                'email_cc': ", ".join(
                    [self.env['hr.employee'].browse(cc).work_email for cc in
                     cc_employees]),
                'email_from': rec.employee_id.work_email,
                "model": 'account.analytic.line',
                "res_id": rec.id}
            template_id.sudo().send_mail(rec.id, force_send=True,
                                         email_values=email_vals)

    def send_employee_daily_work_report(self):
        """A daily work report for all employees will be sent."""
        params = self.env['ir.config_parameter'].sudo()
        work_report = params.get_param(
            'work_report_from_timesheet.report_method')
        if work_report == 'daily_report':
            manager_email = params.get_param(
                'work_report_from_timesheet.employee_id')
            cc_employees = literal_eval(
                params.get_param('work_report_from_timesheet.employee_ids'))
            template_id = self.env.ref('work_report_from_timesheet.'
                                       'email_template_daily_report_from_timesheet')
            email_vals = {
                'message_type': 'notification',
                'is_notification': True,
                'email_to': self.env['hr.employee'].browse(
                    int(manager_email)).work_email,
                'email_cc': ", ".join(
                    [self.env['hr.employee'].browse(cc).work_email for cc in
                     cc_employees]),
                'model': 'account.analytic.line'}
            timesheet = self.env['account.analytic.line'].search(
                [('date', '=', datetime.today().date())])
            employees = list(timesheet.employee_id)
            for employee in employees:
                data = timesheet.filtered(
                    lambda emp: emp.employee_id.id == employee.id)  # pylint: disable=cell-var-from-loop
                email_vals['email_from'] = employee.work_email
                email_vals[
                    'subject'] = f"Daily work report_{datetime.today().date().strftime('%b-%d-%Y')}_{employee.name}"
                res_id = [rec.id for rec in data]
                template_id.with_context(data=data).send_mail(res_id=res_id[0],
                                                              email_values=email_vals,
                                                              force_send=True)

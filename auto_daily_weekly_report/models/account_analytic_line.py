# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import datetime
from odoo import models


class AccountAnalyticLine(models.Model):
    """
    Class inherits account.analytic.line to send the daily and weekly report as
    email.
    """
    _inherit = 'account.analytic.line'

    def create_daily_report(self):
        """
        Method for automatically send email for daily work report.
        """
        employee_ids = self.env['hr.employee'].search(
            [('parent_id.work_email', '!=', False)])
        template = self.env.ref(
            'auto_daily_weekly_report.email_template_daily_report',
            raise_if_not_found=False)
        if not template:
            return

        for employee in employee_ids:
            user_email = (employee.work_email
                          or employee.company_id.email_formatted)

            account_analytic_line_ids = self.env[
                'account.analytic.line'].search(
                [('date', '=', datetime.datetime.today().date()),
                 ('employee_id', '=', employee.id)]
            )

            lines = [{
                'project': record.project_id.name,
                'task': record.task_id.name,
                'description': record.name,
                'hours_spent': record.unit_amount
            } for record in account_analytic_line_ids]

            ctx = {
                'data': lines,
                'from_email': user_email,
                'to_email': employee.parent_id.work_email,
                'employee': employee.name,
            }

            if len(lines) >= 1:
                template.sudo().with_context(**ctx).send_mail(
                    account_analytic_line_ids[0].id,
                    force_send=True
                )

    def create_weekly_report(self):
        """
        Method for automatically send email for weekly task report.
        """
        today_date = datetime.datetime.today()
        week_num = today_date.isocalendar()[1]

        start_date = today_date - datetime.timedelta(
            days=datetime.datetime.today().isoweekday() % 7)

        employee_ids = self.env['hr.employee'].search(
            [('parent_id.work_email', '!=', False)])

        template = self.env.ref(
            'auto_daily_weekly_report.email_template_weekly_report',
            raise_if_not_found=False)
        if not template:
            return

        for employee in employee_ids:
            user_email = (employee.work_email
                          or employee.company_id.email_formatted)

            working_days = employee.resource_calendar_id.attendance_ids.mapped(
                'dayofweek')
            working_days = [int(day) for day in working_days]

            account_analytic_line_ids = self.env[
                'account.analytic.line'].search(
                [('date', '>=', start_date),
                 ('date', '<=', datetime.datetime.today().date()),
                 ('employee_id', '=', employee.id)]
            )

            filtered_records = []
            for line in account_analytic_line_ids:
                if line.date.weekday() in working_days:
                    filtered_records.append(line)

            lines = [{
                'project': record.project_id.name,
                'task': record.task_id.name,
                'description': record.name,
                'hours_spent': record.unit_amount
            } for record in filtered_records]

            ctx = {
                'data': lines,
                'week': f"Week {week_num}, {today_date.year}",
                'from_email': user_email,
                'to_email': employee.parent_id.work_email,
                'employee': employee.name,
            }

            if len(lines) >= 1:
                template.sudo().with_context(**ctx).send_mail(
                    filtered_records[0].id,
                    force_send=True
                )

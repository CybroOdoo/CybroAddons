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
from odoo import api, models


class ReportTimesheet(models.AbstractModel):
    """Create an Abstract Class for report data to pass to the templates"""
    _name = 'report.timesheets_by_employee.report_timesheet_employee'
    _description = 'Timesheet Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Overwriting this function because we need to show values from other
         models in the report. In Odoo 20, report data dictionary is passed
         directly into the QWeb context under the 'data' key, and 'docs' must
         be a valid model recordset."""
        if data is None:
            data = {}
        user_id = data.get('employee')
        from_date = data.get('start_date')
        to_date = data.get('end_date')
        user = self.env['res.users'].browse(user_id) if user_id else self.env.user
        employee = self.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        timesheets = self.get_timesheets(user.id, from_date, to_date)
        company_id = user.company_id
        period = None
        if from_date and to_date:
            period = f"From {from_date} To {to_date}"
        elif from_date:
            period = f"From {from_date}"
        elif to_date:
            period = f"To {to_date}"

        data.update({
            'employee_name': employee.name if employee else user.name,
            'company_name': company_id.name if company_id else '',
            'period': period or 'All',
            'total': timesheets[1],
            'timesheets': timesheets[0],
        })

        return {
            'doc_ids': docids or [user.id],
            'doc_model': 'res.users',
            'docs': user,
            'data': data,
        }

    def get_timesheets(self, user_id, from_date, to_date):
        """Input : user_id, from_date, to_date
        Output: timesheet lines for the employee within the given period and
        the total duration"""
        domain = [('user_id', '=', user_id)]
        if from_date:
            domain.append(('date', '>=', from_date))
        if to_date:
            domain.append(('date', '<=', to_date))
        record = self.env['account.analytic.line'].search(domain)
        records = []
        total = 0
        for rec in record:
            vals = {
                'project': rec.project_id.name or '',
                'user': rec.user_id.partner_id.name or '',
                'duration': rec.unit_amount,
                'date': rec.date,
            }
            total += rec.unit_amount
            records.append(vals)
        return [records, total]

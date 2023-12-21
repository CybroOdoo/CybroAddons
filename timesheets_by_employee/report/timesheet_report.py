# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ajith V (odoo@cybrosys.com)
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
#############################################################################
from odoo import api, models


class ReportTimesheet(models.AbstractModel):
    """Create an Abstract Class for report data to pass to the templates"""
    _name = 'report.timesheets_by_employee.report_timesheet_employee'
    _description = 'Timesheet Report'

    def get_timesheets(self, docs):
        """input : name of employee, the starting date and ending date
        output: timesheet by that particular employee within that period and
        the total duration
        """
        if docs.from_date and docs.to_date:
            record = self.env['account.analytic.line'].search(
                [('user_id', '=', docs.user_id[0].id),
                 ('date', '>=', docs.from_date), ('date', '<=', docs.to_date)])
        elif docs.from_date:
            record = self.env['account.analytic.line'].search(
                [('user_id', '=', docs.user_id[0].id),
                 ('date', '>=', docs.from_date)])
        elif docs.to_date:
            record = self.env['account.analytic.line'].search(
                [('user_id', '=', docs.user_id[0].id),
                 ('date', '<=', docs.to_date)])
        else:
            record = self.env['account.analytic.line'].search(
                [('user_id', '=', docs.user_id[0].id)])
        records = []
        total = 0
        for rec in record:
            vals = {'project': rec.project_id.name,
                    'user': rec.user_id.partner_id.name,
                    'duration': rec.unit_amount,
                    'date': rec.date,
                    }
            total += rec.unit_amount
            records.append(vals)
        return [records, total]

    @api.model
    def _get_report_values(self, docids, data=None):
        """we are overwriting this function because we need to show values from
        other models in the report we pass the objects in the docargs dictionary
        """
        docs = self.env['timesheet.report'].browse(
            self.env.context.get('active_id'))
        identification = []
        for rec in self.env['hr.employee'].search(
                [('user_id', '=', docs.user_id[0].id)]):
            if rec:
                identification.append({'id': rec.id, 'name': rec.name})
        timesheets = self.get_timesheets(docs)
        company_id = self.env['res.company'].search(
            [('name', '=', docs.user_id[0].company_id.name)])
        period = None
        if docs.from_date and docs.to_date:
            period = "From " + str(docs.from_date) + " To " + str(docs.to_date)
        elif docs.from_date:
            period = "From " + str(docs.from_date)
        elif docs.to_date:
            period = "To " + str(docs.to_date)
        if len(identification) > 1:
            return {
                'doc_ids': self.ids,
                'docs': docs,
                'timesheets': timesheets[0],
                'total': timesheets[1],
                'company': company_id,
                'identification': identification,
                'period': period,
                'data': data,
            }
        else:
            return {
                'doc_ids': self.ids,
                'docs': docs,
                'timesheets': timesheets[0],
                'total': timesheets[1],
                'identification': identification,
                'company': company_id,
                'period': period,
            }

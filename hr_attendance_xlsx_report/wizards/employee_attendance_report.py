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
import io
import json
from datetime import datetime, date
from dateutil.rrule import rrule, DAILY

from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import json_default

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class EmployeeAttendanceReport(models.TransientModel):
    """ Wizard for Employee Attendance Report """
    _name = 'employee.attendance.report'
    _description = 'Employee Attendance Report Wizard'

    from_date = fields.Date('From Date', help="Starting date for report")
    to_date = fields.Date('To Date', help="Ending date for report")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
        help='Company for report'
    )
    employee_ids = fields.Many2many(
        'hr.employee', string='Employee',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help='Name of Employee'
    )

    def action_print_xlsx(self):
        """
        Returns report action for the XLSX Attendance report
        Raises: ValidationError: if From Date > To Date
        Raises: ValidationError: if there are no attendance records
        Returns:
            dict:  the XLSX report action
        """
        if not self.from_date:
            self.from_date = date.today()
        if not self.to_date:
            self.to_date = date.today()
        if self.from_date > self.to_date:
            raise ValidationError(_('From Date must be earlier than To Date.'))
        start_datetime = datetime.combine(self.from_date, datetime.min.time())
        end_datetime = datetime.combine(self.to_date, datetime.max.time())
        domain = [
            ('check_in', '>=', start_datetime),
            ('check_in', '<=', end_datetime),
        ]
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        if self.company_id:
            domain.append(('employee_id.company_id', 'in', [self.company_id.id, False]))
        attendances = self.env['hr.attendance'].search(domain)
        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'employee_ids': self.employee_ids.ids,
            'company_id': self.company_id.id if self.company_id else self.env.company.id,
        }
        if self.employee_ids and not attendances:
            raise ValidationError(
                _("There are no attendance records for the employee."))
        if self.from_date and self.to_date:
            return {
                'type': 'ir.actions.report',
                'data': {'model': 'employee.attendance.report',
                         'options': json.dumps(data, default=json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Attendance Report',
                         },
                'report_type': 'xlsx',
            }

    def get_xlsx_report(self, data, response):
        """
        Print the XLSX report
        Returns: None
        """
        self.check_access('read')

        start_date = fields.Date.to_date(data.get('from_date')) or date.today()
        end_date = fields.Date.to_date(data.get('to_date')) or date.today()
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        date_range = list(rrule(DAILY, dtstart=start_date, until=end_date))

        domain = [
            ('check_in', '>=', start_datetime),
            ('check_in', '<=', end_datetime),
        ]
        company_id = data.get('company_id')
        if company_id:
            domain.append(('employee_id.company_id', 'in', [company_id, False]))
        elif self.env.companies:
            domain.append(('employee_id.company_id', 'in', self.env.companies.ids + [False]))

        raw_employee_ids = data.get('employee_ids') or []
        if raw_employee_ids:
            sanitized_ids = [
                int(eid) for eid in raw_employee_ids
                if isinstance(eid, int) or (isinstance(eid, str) and eid.isdigit())
            ]
            allowed_employees = self.env['hr.employee'].search([('id', 'in', sanitized_ids)])
            domain.append(('employee_id', 'in', allowed_employees.ids))

        attendance_groups = self.env['hr.attendance']._read_group(
            domain=domain,
            groupby=['employee_id', 'check_in:day'],
            aggregates=['worked_hours:sum'],
        )

        employee_daily_hours = {}
        for employee, check_in_day, worked_hours in attendance_groups:
            if not employee or not check_in_day:
                continue
            date_key = check_in_day.strftime('%Y-%m-%d') if hasattr(check_in_day, 'strftime') else str(check_in_day)
            employee_daily_hours.setdefault(employee, {})[date_key] = worked_hours

        attendance_list = []
        for employee, daily_hours in employee_daily_hours.items():
            date_sum_list = []
            for date_data in date_range:
                date_out = date_data.strftime('%Y-%m-%d')
                total_hours = daily_hours.get(date_out, 0)
                date_sum_list.append({
                    'name': employee.name,
                    'date': date_out,
                    'sum': total_hours,
                })
            attendance_list.append({
                'name': employee.name,
                'items': date_sum_list,
            })

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('docs')
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 15)
        border = workbook.add_format({'border': 1})
        green = workbook.add_format({'bg_color': '#28A828', 'border': 1})
        red = workbook.add_format({'bg_color': '#ff3333', 'border': 1})
        rose = workbook.add_format({'bg_color': '#DA70D6', 'border': 1})
        head = workbook.add_format(
            {'bold': True, 'font_size': 30, 'align': 'center'})
        date_size = workbook.add_format(
            {'font_size': 12, 'bold': True, 'align': 'center'})
        sheet.merge_range('C3:K6', 'Attendance Report', head)
        sheet.merge_range('B8:C9', 'From Date: ' + str(start_date), date_size)
        sheet.merge_range('B10:C11', 'To Date: ' + str(end_date), date_size)
        sheet.write(2, 12, '', green)
        sheet.write(2, 13, 'Present')
        sheet.write(4, 12, '', red)
        sheet.write(4, 13, 'Absent')
        sheet.write(6, 12, '', rose)
        sheet.write(6, 13, 'Half Day')
        sheet.merge_range('B16:B17', 'Sl.No', border)
        sheet.merge_range('C16:C17', 'Employee', border)
        row = 15
        col = 2
        for date_data in date_range:
            col += 1
            sheet.write(row, col, date_data.strftime('%Y-%m-%d'), border)
        row = 16
        col = 2
        for date_data in date_range:
            col += 1
            sheet.write(row, col, date_data.strftime('%a'), border)

        work = self.env.ref('resource.resource_calendar_std', raise_if_not_found=False)
        hours_per_day = work.hours_per_day if work and work.hours_per_day else 8.0
        half_day_hours = hours_per_day / 2
        row = 17
        i = 0
        for rec in attendance_list:
            row += 1
            col = 1
            i += 1
            sheet.write(row, col, i, border)
            col += 1
            sheet.write(row, col, rec['name'], border)
            for item in rec['items']:
                col += 1
                if item['sum'] >= hours_per_day:
                    sheet.write(row, col, item['sum'], green)
                elif item['sum'] >= half_day_hours:
                    sheet.write(row, col, item['sum'], rose)
                else:
                    sheet.write(row, col, item['sum'], red)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


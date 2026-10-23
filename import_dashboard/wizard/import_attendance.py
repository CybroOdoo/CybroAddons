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
from .import_utils import get_file_content, read_csv_data, read_xlsx_data
from odoo import fields, models
from odoo.exceptions import ValidationError


class ImportAttendance(models.TransientModel):
    """ Model for Attendance import wizard. """
    _name = 'import.attendance'
    _description = 'Attendance Import'

    file_type = fields.Selection(selection=[('csv', 'CSV File'),
                                            ('xls', 'XLS File')], default='csv',
                                 string='Select File Type',
                                 help="Type of the file to import")
    file_upload = fields.Binary(string='Upload File',
                                help="File to import")

    def action_import_attendance(self):
        """Creating attendance record using uploaded xl/csv files"""
        hr_employee = self.env['hr.employee']
        hr_attendance = self.env['hr.attendance']
        datas = {}

        # CSV
        if self.file_type == 'csv':
            try:
                datas = read_csv_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format "
                               "of the file and try again!")
                )

        # XLSX
        if self.file_type == 'xls':
            try:
                datas = read_xlsx_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format of the file and try again!")
                )

        # PROCESS DATA
        for item in datas:
            vals = {}

            # Employee
            if item.get('Employee'):
                employee = hr_employee.search(
                    [('name', '=', item.get('Employee'))], limit=1
                )
                if employee:
                    vals['employee_id'] = employee.id
                else:
                    raise ValidationError(
                        self.env._("There is no employee with that name."
                                   "\n\nPlease check and try again!")
                    )

            # Check In
            if item.get('Check In'):
                if self.file_type == 'csv':
                    vals['check_in'] = item.get('Check In')
                else:
                    # openpyxl already gives datetime
                    vals['check_in'] = item.get('Check In')

            # Check Out
            if item.get('Check Out'):
                if self.file_type == 'csv':
                    vals['check_out'] = item.get('Check Out')
                else:
                    vals['check_out'] = item.get('Check Out')

            # Worked Hours
            if item.get('Worked Hours'):
                vals['worked_hours'] = item.get('Worked Hours')

            hr_attendance.create(vals)

        return {
            'effect': {
                'fadeout': 'slow',
                'message': self.env._('Imported Successfully'),
                'type': 'rainbow_man',
            }
        }

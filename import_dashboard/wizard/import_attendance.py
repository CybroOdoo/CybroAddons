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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import binascii
import csv
import io
import tempfile
import datetime
import openpyxl
from odoo import fields, models
from odoo.exceptions import ValidationError


class ImportAttendance(models.TransientModel):
    """ Model for Attendance import wizard. """
    _name = 'import.attendance'
    _description = 'Attendance Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Select File Type', default='csv',
        help="It helps to select File Type")
    file_upload = fields.Binary(string="Upload File",
                                help="It helps to upload files")

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

    def action_import_attendance(self):
        """Creating attendance record using uploaded xl/csv files"""
        hr_employee = self.env['hr.employee']
        hr_attendance = self.env['hr.attendance']
        datas = {}
        # --- FILE READ ---
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                datas = csv.DictReader(data_file, delimiter=',')
            except Exception:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of the file and try again!"
                )
        elif self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
                rows = list(sheet.rows)
                headers = [cell.value for cell in rows[0]]
                datas = []
                for row in rows[1:]:
                    datas.append({k: v.value for k, v in zip(headers, row)})
            except Exception:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of the file and try again!"
                )
        # --- PROCESS DATA ---
        if datas:
            for item in datas:
                vals = {}
                # --- EMPLOYEE ---
                employee_name = self.get_val(item, 'Employee')
                if employee_name:
                    employee = hr_employee.search(
                        [('name', '=', employee_name)], limit=1
                    )
                    if not employee:
                        raise ValidationError(
                            "There is no employee with that name.\n\nPlease check and try again!"
                        )
                    vals['employee_id'] = employee.id
                # --- CHECK IN ---
                check_in = self.get_val(item, 'Check In')
                if check_in:
                    if self.file_type == 'csv':
                        vals['check_in'] = check_in
                    else:
                        if isinstance(check_in, (datetime.datetime, datetime.date)):
                            vals['check_in'] = check_in
                        else:
                            vals['check_in'] = check_in
                # --- CHECK OUT ---
                check_out = self.get_val(item, 'Check Out')
                if check_out:
                    if self.file_type == 'csv':
                        vals['check_out'] = check_out
                    else:
                        if isinstance(check_out, (datetime.datetime, datetime.date)):
                            vals['check_out'] = check_out
                        else:
                            vals['check_out'] = check_out
                # --- WORKED HOURS ---
                vals['worked_hours'] = self.get_val(
                    item,
                    'Worked Hours',
                    default=0.0
                )
                # --- CREATE RECORD ---
                if vals.get('employee_id') and vals.get('check_in'):
                    hr_attendance.create(vals)
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Imported Successfully',
                    'type': 'rainbow_man',
                }
            }
        return False

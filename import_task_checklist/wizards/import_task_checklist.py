# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import base64
import csv
import io

import xlrd

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ImportTaskCheckList(models.TransientModel):
    """To import task checklist,
      here we can upload the files csv or xlsx format"""
    _name = 'import.task.checklist'
    _description = 'Import Task checklist from excel and csv'

    file_type = fields.Selection([('csv', 'CSV File'), ('xls', 'EXCEL File')],
                                 string='Import File Type', default='csv',
                                 help="Here we can choose the type of the file")
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.company,
                                 help="To get the current company")
    file_content = fields.Binary(string='File Content', attachment=True,
                                 required=True, help="To upload the file")
    filename = fields.Char(string='File Name', required=True,
                           help="To get the file name")

    def action_import_task_checklist_xlsx(self):
        """To import task checklist in xlsx or xls format,
         it will create a new checklist from this file"""
        try:
            file_data = base64.b64decode(self.file_content)
        except Exception:
            raise UserError(_('Failed to decode the uploaded file.'))

        sheets_data = []

        # Try openpyxl first (for .xlsx files)
        try:
            import openpyxl
            book = openpyxl.load_workbook(io.BytesIO(file_data), data_only=True)
            for sheet in book.worksheets:
                for row_idx, row in enumerate(sheet.rows, 1):
                    if row_idx > 1:
                        row_values = [cell.value for cell in row]
                        if any(val is not None and str(val).strip() for val in row_values):
                            formatted_values = []
                            for val in row_values:
                                if val is None:
                                    formatted_values.append('')
                                elif isinstance(val, float) and val % 1 == 0:
                                    formatted_values.append(str(int(val)))
                                else:
                                    formatted_values.append(str(val))
                            sheets_data.append(formatted_values)
        except Exception:
            # Fallback to xlrd (for .xls files)
            try:
                book = xlrd.open_workbook(file_contents=file_data)
                for sheet in book.sheets():
                    for row_idx in range(1, sheet.nrows):
                        row_values = sheet.row_values(row_idx)
                        if any(val != '' for val in row_values):
                            formatted_values = []
                            for val in row_values:
                                if val is None:
                                    formatted_values.append('')
                                elif isinstance(val, float) and val % 1 == 0:
                                    formatted_values.append(str(int(val)))
                                else:
                                    formatted_values.append(str(val))
                            sheets_data.append(formatted_values)
            except Exception:
                raise UserError(_('Only excel files (.xls or .xlsx) are supported.'))

        if not sheets_data:
            raise UserError(_('The uploaded file is empty or does not contain any valid rows.'))

        # Extract names and descriptions, handling potential indexing safety
        rows_to_process = []
        names_to_check = []
        for row in sheets_data:
            if len(row) < 3:
                raise UserError(_('Each row in the Excel file must contain at least 3 columns (Serial, Description, Name).'))
            name = row[2].strip() if row[2] else ''
            description = row[1].strip() if row[1] else ''
            if not name:
                continue
            rows_to_process.append((name, description))
            names_to_check.append(name)

        if not names_to_check:
            raise UserError(_('No valid checklist names found in the Excel file.'))

        # Bulk search to avoid N+1 queries
        existing_checklists = self.env['task.checklist'].sudo().search([
            ('name', 'in', names_to_check)
        ])
        existing_names = set(existing_checklists.mapped('name'))

        # Create missing records
        for name, description in rows_to_process:
            if name not in existing_names:
                self.env['task.checklist'].sudo().create({
                    'name': name,
                    'description': description,
                    'company_id': self.company_id.id,
                })
                existing_names.add(name)

        message = _("Successfully Imported!")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }


    def action_import_task_checklist_csv(self):
        """To import task checklist in csv format,
         it will create a new checklist from this file"""
        try:
            file_data = base64.b64decode(self.file_content).decode("utf-8-sig")
        except Exception:
            raise UserError(_('Failed to decode the file: Only CSV files are supported.'))

        try:
            data = io.StringIO(file_data)
            csv_reader = csv.reader(data, delimiter=',')
            file_reader = list(csv_reader)
        except Exception as e:
            raise UserError(_('Malformed CSV file structure: %s') % e)

        if not file_reader or len(file_reader) <= 1:
            raise UserError(_('The CSV file is empty or contains only a header row.'))

        # Remove header row
        file_reader.pop(0)

        rows_to_process = []
        names_to_check = []
        for line_no, row in enumerate(file_reader, start=2):
            if not row or not any(row):
                continue
            if len(row) < 3:
                raise UserError(_('Each row in the CSV file must contain at least 3 columns (Serial, Description, Name).'))
            name = row[2].strip() if row[2] else ''
            description = row[1].strip() if row[1] else ''
            if not name:
                continue

            rows_to_process.append((name, description))
            names_to_check.append(name)

        if not names_to_check:
            raise UserError(_('No valid checklist names found in the CSV file.'))

        # Bulk search to avoid N+1 queries
        existing_checklists = self.env['task.checklist'].sudo().search([
            ('name', 'in', names_to_check)
        ])
        existing_names = set(existing_checklists.mapped('name'))

        # Create missing records
        for name, description in rows_to_process:
            if name not in existing_names:
                self.env['task.checklist'].sudo().create({
                    'name': name,
                    'description': description,
                    'company_id': self.company_id.id,
                })
                existing_names.add(name)

        message = _("Successfully Imported!")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

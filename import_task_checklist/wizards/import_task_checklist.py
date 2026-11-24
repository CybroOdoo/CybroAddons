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
import base64
import csv
import io
import logging
import openpyxl
import xlrd
from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


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
    filename = fields.Char(string='File Name',
                           help="To get the file name")

    def _get_file_bytes(self):
        """Extract raw bytes from Binary field in Odoo 20"""
        if not self.file_content:
            return b''
        if hasattr(self.file_content, 'content'):
            return self.file_content.content
        if isinstance(self.file_content, (bytes, bytearray)):
            return bytes(self.file_content)
        if isinstance(self.file_content, str):
            try:
                return base64.b64decode(self.file_content)
            except Exception:
                return self.file_content.encode('utf-8')
        try:
            return bytes(self.file_content)
        except Exception:
            return b''

    def _get_file_text(self):
        """Extract decoded string for CSV parsing"""
        raw_bytes = self._get_file_bytes()
        return raw_bytes.decode('utf-8-sig', errors='replace')

    def _process_import_rows(self, rows):
        """Unified parser for CSV and Excel rows.
        Dynamically matches headers for Name, Description, Company, and Checklist Items.
        """
        if not rows:
            raise UserError(_('The uploaded file is empty.'))

        first_row = [str(cell).strip() if cell is not None else '' for cell in rows[0]]
        first_row_lower = [c.lower() for c in first_row]

        col_name = None
        col_desc = None
        col_company = None
        col_item_name = None
        col_item_desc = None

        has_header = False

        # Header detection
        for idx, col_title in enumerate(first_row_lower):
            if not col_title:
                continue
            if 'checklist item' in col_title or 'checklist_ids' in col_title or 'item' in col_title:
                has_header = True
                if 'description' in col_title or 'desc' in col_title:
                    if col_item_desc is None:
                        col_item_desc = idx
                else:
                    if col_item_name is None:
                        col_item_name = idx
            elif 'name' in col_title or 'checklist' in col_title or 'title' in col_title:
                has_header = True
                if col_name is None:
                    col_name = idx
            elif 'description' in col_title or 'desc' in col_title:
                has_header = True
                if col_desc is None:
                    col_desc = idx
            elif 'company' in col_title:
                has_header = True
                if col_company is None:
                    col_company = idx

        data_rows = rows
        if has_header:
            data_rows = rows[1:]

        # Positional fallbacks when headers are absent
        if col_name is None:
            if len(first_row) >= 3 and not has_header:
                if first_row[0].isdigit():
                    col_name = 2
                    col_desc = 1
                else:
                    col_name = 0
                    col_desc = 1
                    col_company = 2
            else:
                col_name = 0
                if len(first_row) > 1:
                    col_desc = 1

        checklists_data = {}
        last_checklist_name = None

        for row in data_rows:
            if not row or not any(str(c).strip() for c in row if c is not None):
                continue

            def get_cell(index):
                if index is not None and index < len(row):
                    val = row[index]
                    return str(val).strip() if val is not None else ''
                return ''

            c_name = get_cell(col_name)
            c_desc = get_cell(col_desc)
            i_name = get_cell(col_item_name)
            i_desc = get_cell(col_item_desc)

            if c_name:
                last_checklist_name = c_name
            elif last_checklist_name:
                c_name = last_checklist_name

            if not c_name:
                continue

            if c_name not in checklists_data:
                checklists_data[c_name] = {
                    'description': c_desc,
                    'items': []
                }
            elif c_desc and not checklists_data[c_name]['description']:
                checklists_data[c_name]['description'] = c_desc

            # Add checklist items if present in row
            if i_name or i_desc:
                checklists_data[c_name]['items'].append({
                    'name': i_name or str(len(checklists_data[c_name]['items']) + 1),
                    'description': i_desc or i_name
                })

        if not checklists_data:
            raise UserError(_('No valid task checklist records found in the uploaded file.'))

        ChecklistEnv = self.env['task.checklist']
        ItemEnv = self.env['checklist.item']

        created_count = 0
        updated_count = 0
        items_created_count = 0

        for chk_name, chk_info in checklists_data.items():
            search_domain = [('name', '=', chk_name)]
            if self.company_id:
                search_domain.append(('company_id', '=', self.company_id.id))
            existing = ChecklistEnv.search(search_domain, limit=1)
            if not existing:
                checklist = ChecklistEnv.create({
                    'name': chk_name,
                    'description': chk_info['description'],
                    'company_id': self.company_id.id if self.company_id else False,
                })
                created_count += 1
            else:
                checklist = existing
                if chk_info['description'] and not checklist.description:
                    checklist.write({'description': chk_info['description']})
                updated_count += 1

            # Create items for this checklist
            existing_item_names = set(checklist.checklist_ids.mapped('name'))
            existing_item_descs = set(checklist.checklist_ids.mapped('description'))

            for seq, item_info in enumerate(chk_info['items'], start=1):
                iname = item_info['name']
                idesc = item_info['description']
                if iname not in existing_item_names or (idesc and idesc not in existing_item_descs):
                    ItemEnv.create({
                        'checklist_id': checklist.id,
                        'name': iname,
                        'description': idesc,
                        'sequence': seq,
                    })
                    existing_item_names.add(iname)
                    if idesc:
                        existing_item_descs.add(idesc)
                    items_created_count += 1

        if created_count == 0 and items_created_count == 0:
            message = _("No new records were imported because all entries already exist.")
            notification_type = 'warning'
        else:
            message = _("Successfully imported!")
            notification_type = 'success'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': notification_type,
                'sticky': False,
            }
        }

    def action_import_task_checklist_xlsx(self):
        """To import task checklist in xlsx or xls format"""
        if self.filename:
            ext = self.filename.lower().split('.')[-1] if '.' in self.filename else ''
            if ext not in ('xls', 'xlsx'):
                raise UserError(
                    _('Invalid file format "%s". EXCEL file is selected, '
                      'but the uploaded file is not an Excel file (.xls or .xlsx).',
                      self.filename)
                )
        file_data = self._get_file_bytes()
        if not file_data:
            raise UserError(_('The uploaded file is empty or missing content.'))

        all_rows = []
        openpyxl_err = None
        try:
            book = openpyxl.load_workbook(io.BytesIO(file_data), data_only=True)
            for sheet in book.worksheets:
                for row in sheet.rows:
                    row_values = [cell.value for cell in row]
                    if any(val is not None and str(val).strip() for val in row_values):
                        all_rows.append(row_values)
        except Exception as e:
            openpyxl_err = e

        if not all_rows:
            try:
                book = xlrd.open_workbook(file_contents=file_data)
                for sheet in book.sheets():
                    for row_idx in range(sheet.nrows):
                        row_values = sheet.row_values(row_idx)
                        if any(val != '' for val in row_values):
                            all_rows.append(row_values)
            except Exception as e:
                raise UserError(
                    _('Only Excel files (.xls or .xlsx) are supported. Error: %s',
                      (openpyxl_err or e))
                )

        return self._process_import_rows(all_rows)

    def action_import_task_checklist_csv(self):
        """To import task checklist in csv format"""
        if self.filename:
            ext = self.filename.lower().split('.')[-1] if '.' in self.filename else ''
            if ext != 'csv':
                raise UserError(
                    _('Invalid file format "%s". CSV file is selected, '
                      'but the uploaded file is not a CSV file (.csv).',
                      self.filename)
                )
        file_text = self._get_file_text()
        if not file_text:
            raise UserError(_('The uploaded file is empty or missing content.'))

        try:
            data = io.StringIO(file_text)
            csv_reader = csv.reader(data, delimiter=',')
            all_rows = list(csv_reader)
        except Exception as e:
            raise UserError(_('Malformed CSV file structure: %s', e))

        return self._process_import_rows(all_rows)


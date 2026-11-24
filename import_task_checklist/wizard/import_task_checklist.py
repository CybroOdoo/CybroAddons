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
#    This program is distributed in the hope it will be useful,
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
from io import BytesIO

from openpyxl import load_workbook

from odoo import fields, models
from odoo.exceptions import UserError


class ImportTaskCheckList(models.TransientModel):
    """To import task checklist,
      here we can upload the files csv or xlsx format"""
    _name = 'import.task.checklist'
    _description = 'Import Task checklist from excel and csv'

    file_type = fields.Selection(
        [('csv', 'CSV File'), ('xls', 'EXCEL File')],
        string='Import File Type', default='csv',
        help="Here we can choose the type of the file")
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company,
        help="To get the current company")
    file_content = fields.Binary(
        attachment=True, required=True, help="To upload the file")
    filename = fields.Char(
        string='File Name', required=True, help="To get the file name")

    def _create_checklists(self, rows):
        """Create checklists and checklist items from horizontal single-row format.
        Layout:
        Col 0: Checklist Name
        Col 1: Checklist Description
        Col 2: Company Name (optional, falls back to wizard company / active company)
        Col 3+: Checklist Item 1, Checklist Item 2, Checklist Item 3, ...
        """
        checklist_model = self.env['task.checklist']
        item_model = self.env['checklist.item']
        company_model = self.env['res.company']

        for row in rows:
            if not row:
                continue
            name = str(row[0]).strip() if len(row) > 0 and row[0] is not None else ''
            if not name:
                continue

            description = (str(row[1]).strip()
                           if len(row) > 1 and row[1] is not None and str(row[1]).strip()
                           else False)

            company_name = (str(row[2]).strip()
                            if len(row) > 2 and row[2] is not None and str(row[2]).strip()
                            else '')

            company = self.company_id or self.env.company
            if company_name:
                found_company = company_model.search([('name', '=ilike', company_name)], limit=1)
                if found_company:
                    company = found_company

            checklist = checklist_model.with_company(company).search([
                ('name', '=', name),
                ('company_id', '=', company.id),
            ], limit=1)
            if not checklist:
                checklist = checklist_model.with_company(company).create({
                    'name': name,
                    'description': description or False,
                    'company_id': company.id,
                })
            elif description and not checklist.description:
                checklist.write({'description': description})

            # Process all subsequent columns as checklist items in order
            sequence = 1
            for col in row[3:]:
                if col is None:
                    continue
                item_name = str(col).strip()
                if not item_name:
                    continue
                existing_item = item_model.search([
                    ('name', '=', item_name),
                    ('checklist_id', '=', checklist.id),
                ], limit=1)
                if not existing_item:
                    item_model.create({
                        'name': item_name,
                        'checklist_id': checklist.id,
                        'sequence': sequence,
                    })
                sequence += 1

    def _success_notification(self):
        """Return the success notification action."""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': self.env._("Successfully Imported!"),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'}
            }
        }

    def action_import_task_checklist_xlsx(self):
        """To import task checklist in xlsx format,
         it will create a new checklist from this file"""
        if not self.file_content:
            raise UserError(self.env._("Please upload an Excel file."))
        try:
            file_content = base64.b64decode(self.file_content)
            workbook = load_workbook(filename=BytesIO(file_content),
                                     data_only=True)
        except Exception as error:
            raise UserError(
                self.env._("Only excel files are supported.")) from error
        rows = []
        for sheet in workbook.worksheets:
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row or not any(row):
                    continue
                rows.append(list(row))
        self._create_checklists(rows)
        return self._success_notification()

    def action_import_task_checklist_csv(self):
        """To import task checklist in csv format,
         it will create a new checklist from this file"""
        if not self.file_content:
            raise UserError(self.env._("Please upload a CSV file."))
        try:
            file_data = base64.b64decode(self.file_content)
            data = io.StringIO(file_data.decode("utf-8-sig"))
            csv_rows = list(csv.reader(data, delimiter=','))
        except Exception as error:
            raise UserError(
                self.env._("Invalid CSV file.\n%s", str(error))) from error
        if not csv_rows:
            raise UserError(self.env._("The CSV file is empty."))
        # Skip the header row
        rows = [row for row in csv_rows[1:] if row and any(row)]
        self._create_checklists(rows)
        return self._success_notification()

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import xlrd
from datetime import date
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImportTask(models.TransientModel):
    """For handling importing of tasks"""
    _name = 'import.task'
    _description = 'Importing of task'

    name = fields.Char(string="Name", help="Name", default="Import Tasks")
    file_type = fields.Selection([('csv', 'CSV File'),
                                  ('xls', 'XLS File')],
                                 string='Select File Type', default='csv',
                                 help='File type')
    file_upload = fields.Binary(string="Upload File", help="Upload your file")
    user_id = fields.Many2one('res.users', string='Assigned to',
                              help="assigned to user")

    def make_json_dict(self, column, row):
        """"Converting json data to dictionary"""
        return [{col: item[i] for i, col in enumerate(column)} for item in row]

    def action_task_import(self):
        """Creating task record using uploaded xl/csv files"""
        res_partner = self.env['res.partner']
        project_project = self.env['project.project']
        project_task = self.env['project.task']
        datas = {}
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                datas = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!"))
        if self.file_type == 'xls':
            try:
                book_dict = {}
                fp = tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                book = xlrd.open_workbook(fp.name)
                sheets = book.sheets()
                for sheet in sheets:
                    book_dict[sheet.name] = {}
                    columns = sheet.row_values(0)
                    rows = []
                    for row_index in range(1, sheet.nrows):
                        row = sheet.row_values(row_index)
                        rows.append(row)
                    sheet_data = self.make_json_dict(columns, rows)
                    book_dict[sheet.name] = sheet_data
                datas = book_dict['Sheet1']
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!"))
        for item in datas:
            vals = {}
            if item.get('Project'):
                project = project_project.search(
                    [('name', '=', item.get('Project'))])
                if not project:
                    project = project_project.create({
                        'name': item.get('Project')
                    })
                vals['project_id'] = project.id
            if item.get('Title'):
                vals['name'] = item.get('Title')
            if item.get('Customer'):
                partner = res_partner.search(
                    [['name', '=', item.get('Customer')]])
                if not partner:
                    partner = res_partner.create({
                        'name': item.get('Customer')
                    })
                vals['partner_id'] = partner.id
            if item.get('Deadline'):
                if self.file_type == 'xlsx':
                    vals['date_deadline'] = date.fromordinal(
                        date(1900, 1, 1).toordinal() + int(
                            item.get('Deadline')) - 2)
                else:
                    vals['date_deadline'] = item.get('Deadline')
            if item.get('Parent Task'):
                vals['parent_id'] = project_task.search(
                    [('name', '=', item.get('Parent Task'))])
            vals['user_ids'] = self.user_id
            project_task.create(vals)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Imported Successfully',
                'type': 'rainbow_man',
            }
        }

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
import csv
import io
import xlrd
from odoo import fields, models, _
from odoo.exceptions import UserError


class ProjectTaskChecklistImport(models.TransientModel):
    """Task custom checklist import wizard."""
    _name = "project.task.checklist.import"
    _description = "Task custom checklist import"

    file = fields.Binary(string='Upload Your File Here',
                         help="FOr updating the file", required=True)
    file_type = fields.Selection([('excel', 'Excel'), ('csv', 'CSV')],
                                 required=True, string="File type",
                                 help="For determine the file type")
    company_id = fields.Many2one('res.company', string="company",
                                 help="For getting company details",
                                 default=lambda self: self.env.company.id)
    download_sample_file = fields.Boolean(
        string="Download Sample File",
        help="For downloading sample excel or csv file ")

    def import_custom_checklist(self):
        """ function to import task custom checklist using excel and csv"""
        if self.file_type == 'excel':
            book = xlrd.open_workbook(
                file_contents=base64.decodebytes(self.file))
            row_value = []
            for sheet in book.sheets():
                for row in range(1, sheet.nrows):
                    row_value.append(sheet.row_values(row))
            for row in row_value:
                self.env['project.task.checklist'].create({
                    'name': row[0],
                    'description': row[1],
                    'company_id': self.company_id.id
                })
        elif self.file_type == 'csv':
            row_value = []
            csv_data = base64.b64decode(self.file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            file_reader.extend(csv_reader)
            for row in range(1, len(file_reader)):
                row_value.append(file_reader[row])
            for row in row_value:
                self.env['project.task.checklist'].create({
                    'name': row[0],
                    'description': row[1],
                    'company_id': self.company_id.id
                })
        else:
            raise UserError(_("Please check the file you have uploaded"))

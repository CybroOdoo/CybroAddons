# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Thasni CP (odoo@cybrosys.com)
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
##################################################################
import base64
import csv
import io
import xlrd
from odoo import fields, models, _
from odoo.exceptions import UserError


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
        """To import task checklist in xlsx format,
         it will create a new checklist from this file"""
        try:
            book = xlrd.open_workbook(
                file_contents=(base64.decodebytes(self.file_content)))
        except xlrd.biffh.XLRDError:
            raise UserError(_('Only excel files are supported.'))
        for sheet in book.sheets():
            for row in range(sheet.nrows):
                if row >= 1:
                    row_values = sheet.row_values(row)
                    main = self.env['task.checklist'].sudo().search(
                        [('name', '=', row_values[1])])
                    name = main.mapped('name')
                    if row_values[1] not in name:
                        self.env['task.checklist'].sudo().create({
                            'name': row_values[0],
                            'description': row_values[1],
                        })
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
            file = base64.b64decode(self.file_content)
            data = io.StringIO(file.decode("utf-8"))
            data.seek(0)
            file_reader = []
            csv_reader = csv.reader(data, delimiter=',')
            file_reader.extend(csv_reader)
            file_reader.pop(0)
            for row in file_reader:
                main = self.env['task.checklist'].sudo().search(
                    [('name', '=', row[1])])
                name = main.mapped('name')
                if row[1] not in name:
                    self.env['task.checklist'].sudo().create({
                        'name': row[0],
                        'description': row[1],
                    })
        except:
            raise UserError(_('Only csv files are supported.'))
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

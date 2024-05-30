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
import datetime
from odoo.exceptions import ValidationError
from odoo import fields, models


class ImportTask(models.TransientModel):
    """ Model for import project task. """
    _name = 'import.task'
    _description = 'Task Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xls', 'XLS File')], default='csv',
        string='Select File Type', help='File type')
    file_upload = fields.Binary(string="Upload File",
                                help="Helps to upload your file")
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned to',
                              help="assigned to user")

    def action_import_task(self):
        """Creating task record using uploaded xl/csv files"""
        res_partner = self.env['res.partner']
        project_project = self.env['project.project']
        project_task = self.env['project.task']
        items = False
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!")
            items = csv_reader
        if self.file_type == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of "
                    "the file and try again!")
            headers = sheet.row_values(0)  # list
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)  # list
                data += [{k: v for k, v in zip(headers, row)}]
            items = data
        imported = 0
        info_msg = ""
        error_msg = ""
        for item in items:
            vals = {}
            if item.get('Project'):
                project = project_project.search(
                    [('name', '=', item.get('Project'))])
                if not project:
                    project = project_project.create({
                        'name': item.get('Project')
                    })
                    info_msg += f"\nCreated new project with name :{item.get('Project')}"
                vals['project_id'] = project.id
            if item.get('Title'):
                vals['name'] = item.get('Title')
            else:
                error_msg += "⚠Title missing in file!"
            if item.get('Customer'):
                partner = res_partner.search(
                    [['name', '=', item.get('Customer')]])
                if not partner:
                    partner = res_partner.create({
                        'name': item.get('Customer')
                    })
                    info_msg += f"\nCreated new partner with name :{item.get('Customer')}"
                vals['partner_id'] = partner.id
            if item.get('Deadline'):
                vals['date_deadline'] = datetime.datetime.strptime(
                    item.get('Deadline'), '%m/%d/%Y')
            if item.get('Parent Task'):
                parent_task = project_task.search(
                    [('name', '=', item.get('Parent Task'))])
                if len(parent_task) > 1:
                    parent_task = parent_task[0]
                vals['parent_id'] = parent_task.id
            vals['user_ids'] = self.user_id
            if error_msg:
                error_msg = "\n\n🏮 ERROR 🏮" + error_msg
                error_message = self.env['import.message'].create(
                    {'message': error_msg})
                return {
                    'name': 'Error!',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'import.message',
                    'res_id': error_message.id,
                    'target': 'new'
                }
            task_id = project_task.create(vals)
            if task_id:
                imported += 1
            if info_msg:
                info_msg = f"\nInformation : {info_msg}"
            msg = (("Imported %d records."
                    % imported) + info_msg)
            message = self.env['import.message'].create(
                {'message': msg})
            if message:
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': msg,
                        'type': 'rainbow_man',
                    }
                }

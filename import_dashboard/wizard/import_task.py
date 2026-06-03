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
import openpyxl
import datetime
from odoo.exceptions import ValidationError
from odoo import fields, models


class ImportTask(models.TransientModel):
    """ Model for import project task. """
    _name = 'import.task'
    _description = 'Task Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')], default='csv',
        string='Select File Type', help='File type')
    file_upload = fields.Binary(string="Upload File",
                                help="Helps to upload your file")
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned to',
                              help="assigned to user")

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

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
        if self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of "
                    "the file and try again!")
            rows = list(sheet.rows)
            headers = [cell.value for cell in rows[0]]
            data = []
            for row in rows[1:]:
                data += [{k: v.value for k, v in zip(headers, row)}]
            items = data
        imported = 0
        info_msg = ""
        error_msg = ""
        if items:
            for item in items:
                vals = {}
                project_name = self.get_val(item, 'Project')
                if project_name:
                    project = project_project.search(
                        [('name', '=', project_name)])
                    if not project:
                        project = project_project.create({
                            'name': project_name
                        })
                        info_msg += f"\nCreated new project with name :{project_name}"
                    vals['project_id'] = project.id
                title = self.get_val(item, 'Title')
                if title:
                    vals['name'] = title
                else:
                    error_msg += "⚠Title missing in file!"
                customer_name = self.get_val(item, 'Customer', 'Partner')
                if customer_name:
                    partner = res_partner.search(
                        [['name', '=', customer_name]])
                    if not partner:
                        partner = res_partner.create({
                            'name': customer_name
                        })
                        info_msg += f"\nCreated new partner with name :{customer_name}"
                    vals['partner_id'] = partner.id
                deadline = self.get_val(item, 'Deadline')
                if deadline:
                    vals['date_deadline'] = datetime.datetime.strptime(
                        deadline, '%m/%d/%Y')
                parent_task_name = self.get_val(item, 'Parent Task')
                if parent_task_name:
                    parent_task = project_task.search(
                        [('name', '=', parent_task_name)])
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
        return False

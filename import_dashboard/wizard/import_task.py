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
import datetime
import logging
from .import_utils import get_file_content, read_csv_data, read_xlsx_data
from odoo.exceptions import ValidationError
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ImportTask(models.TransientModel):
    """ Model for import project task. """
    _name = 'import.task'
    _description = 'Task Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xls', 'XLS File')], default='csv',
        string='Select File Type', help='Type of the file to import')
    file_upload = fields.Binary(string="Upload File",
                                help="File to import")
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned To',
                              help="User the imported tasks are assigned to")

    DATE_PATTERNS = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
        "%Y.%m.%d", "%d.%m.%Y", "%m.%d.%Y",
        "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
        "%Y/%m/%d", "%Y %m %d"
    ]

    def _parse_date_value(self, value):
        if value is None:
            return False
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, (int, float)):
            try:
                base = datetime.datetime(1899, 12, 30)
                return (base + datetime.timedelta(days=float(value))).date()
            except Exception:
                _logger.debug("Could not parse date value %r", value, exc_info=True)
        s = str(value).strip()
        if not s:
            return False
        try:
            return datetime.date.fromisoformat(s)
        except Exception:
            _logger.debug("Could not parse date value %r", value, exc_info=True)
        for fmt in self.DATE_PATTERNS:
            try:
                return datetime.datetime.strptime(s, fmt).date()
            except Exception:
                continue
        return False

    def action_import_task(self):
        """Creating task record using uploaded xl/csv files"""
        res_partner = self.env['res.partner']
        project_project = self.env['project.project']
        project_task = self.env['project.task']
        items = []
        if self.file_type == 'csv':
            try:
                items = read_csv_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format "
                               "of the file and try again!"))
        if self.file_type == 'xls':
            try:
                items = read_xlsx_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format of "
                               "the file and try again!"))
        imported = 0
        info_msg = ""
        error_msg = ""
        if items:
            for item in items:
                vals = {}
                if item.get('Project'):
                    project = project_project.search(
                        [('name', '=', item.get('Project'))])
                    if not project:
                        project = project_project.create({
                            'name': item.get('Project')
                        })
                        info_msg += self.env._("\nCreated new project with name: %(value0)s", value0=item.get('Project'))
                    vals['project_id'] = project.id
                if item.get('Title'):
                    vals['name'] = item.get('Title')
                else:
                    error_msg += self.env._("\nTitle missing in file!")
                    continue
                if item.get('Customer'):
                    partner = res_partner.search(
                        [('name', '=', item.get('Customer'))])
                    if not partner:
                        partner = res_partner.create({
                            'name': item.get('Customer')
                        })
                        info_msg += self.env._("\nCreated new partner with name: %(value0)s", value0=item.get('Customer'))
                    vals['partner_id'] = partner.id
                if item.get('Deadline'):
                    parsed_deadline = self._parse_date_value(item.get('Deadline'))
                    if parsed_deadline:
                        vals['date_deadline'] = parsed_deadline
                if item.get('Parent Task'):
                    parent_task = project_task.search(
                        [('name', '=', item.get('Parent Task'))])
                    if len(parent_task) > 1:
                        parent_task = parent_task[0]
                    vals['parent_id'] = parent_task.id
                if self.user_id:
                    vals['user_ids'] = [self.user_id.id]
                task_id = project_task.create(vals)
                if task_id:
                    imported += 1

        if error_msg:
            error_msg = self.env._("\n\nERROR") + error_msg
            error_message = self.env['import.message'].create(
                {'message': error_msg})
            return {
                'name': self.env._('Error!'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'import.message',
                'res_id': error_message.id,
                'target': 'new'
            }
        if info_msg:
            info_msg = self.env._("\nInformation : %(info_msg)s", info_msg=info_msg)
        msg = ((self.env._("Imported %d records.", imported)) + info_msg)
        message = self.env['import.message'].sudo().create(
            {'message': msg})
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': msg,
                    'type': 'rainbow_man',
                }
            }

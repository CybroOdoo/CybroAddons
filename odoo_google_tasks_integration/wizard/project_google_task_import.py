# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
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
#############################################################################
import requests
from odoo import fields, models
from odoo.tools.translate import _
from datetime import datetime

TIMEOUT = 20


class ProjectGoogleTaskImport(models.Model):
    """Model for the Google Task Import Wizard"""
    _name = 'project.google.task.import'
    _description = 'Google Task Import'

    task_ids = fields.Many2many('project.task',
                                string='Select Tasks For Export to Google Task'
                                , help='Tasks to be exported to Google Task')

    export_import_selection = fields.Selection([
        ('import', 'Import from Google Task'),
        ('export', 'Export to Google Task')],
        string='Select Action', default='import',
        help='Choose whether to import tasks from Google Task or export tasks to Google Task')

    def action_import_tasks(self):
        """Import tasks from Google Task."""
        company_id = self.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data')
        url = f"https://tasks.googleapis.com/tasks/v1/lists/@default/tasks"
        headers = {
            "Authorization": f"Bearer {company_id._get_access_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            tasks = response.json().get('items', [])
            imported_count = 0
            for task_data in tasks:
                task_id = self.env['project.task'].search(
                    [('google_task', '=', task_data['id'])])
                due_date = task_data.get('due')
                parsed_date = False
                if due_date:
                    try:
                        parsed_date = datetime.strptime(due_date, '%Y-%m-%dT%H:%M:%S.000Z')
                        parsed_date = parsed_date.strftime('%Y-%m-%d')
                    except ValueError as e:
                        pass
                if not task_id:
                    self.env['project.task'].create({
                        'name': task_data['title'],
                        'date_deadline': parsed_date,
                        'google_task': task_data['id'],
                        'is_imported': True,
                    })
                    imported_count += 1
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Successful'),
                    'type': 'success',
                    'message': _('Imported %s tasks from Google Task.') % imported_count,
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Not Successful!'),
                    'message': _('Error: %s') % response.text,
                    'type': 'warning',
                    'sticky': True,
                }
            }

    def action_export_task(self):
        """Export tasks to Google Task."""
        for task in self.task_ids:
            task.action_sync_task_to_google()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Export Successful'),
                'type': 'success',
                'message': _('Tasks exported to Google Task successfully!'),
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

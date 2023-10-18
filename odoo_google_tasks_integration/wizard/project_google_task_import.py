# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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
from odoo import fields, models, _


class ProjectGoogleTaskImportWizard(models.Model):
    """Model for the Google Task Import Wizard"""
    _name = 'project.google.task.import'
    _description = 'Google Task Import'

    task_ids = fields.Many2many('project.task',
                                string='Select Tasks For Export to Google Task'
                                , help='Tasks to be exported to Google Task')

    def action_import_tasks(self):
        """Import tasks from Google Task."""
        company_id = self.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data')
        url = f"https://tasks.googleapis.com/tasks/v1/lists/@default/" \
              f"tasks?key={company_id.hangout_company_api_key}"
        headers = {
            "Authorization": f"Bearer {company_id.hangout_company_access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tasks = response.json().get('items', [])
            for task_data in tasks:
                task_id = self.env['project.task'].search(
                    [('google_task', '=', task_data['id'])])
                if not task_id:
                    task_id = self.env['project.task'].create({
                        'name': task_data['title'],
                        'date_deadline': task_data['due'],
                        'google_task': task_data['id'],
                        'is_imported': True,
                    })
                    notification = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Successful'),
                            'type': 'success',
                            'message': 'Imported successfully!',
                            'sticky': True,
                        }
                    }
                    return notification, task_id
                action = self.env.ref(
                    'google_tasks_integration.action_project_task').read()[0]
                return action

    def action_export_task(self):
        """Export tasks to Google Task."""
        for task in self.task_ids:
            task.action_sync_task_to_google()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Successful'),
                'type': 'success',
                'message': 'Exported successfully!',
                'sticky': True,
            }
        }

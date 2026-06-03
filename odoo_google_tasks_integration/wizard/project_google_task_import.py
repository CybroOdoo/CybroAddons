# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<http://www.cybrosys.com>)
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
from datetime import datetime

TIMEOUT = 20

class ProjectGoogleTaskImportWizard(models.TransientModel):
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
        url = "https://tasks.googleapis.com/tasks/v1/lists/@default/tasks"
        headers = {
            "Authorization": f"Bearer {company_id.hangout_company_access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers ,timeout=TIMEOUT)
        if response.status_code == 401:
            company_id.action_google_task_company_refresh_token()
            headers["Authorization"] = f"Bearer {company_id.hangout_company_access_token}"
            response = requests.get(url, headers=headers ,timeout=TIMEOUT)

        if response.status_code == 200:
            tasks = response.json().get('items', [])
            task_map = {}

            # First pass: Create or update tasks
            for task_data in tasks:
                task_id = self.env['project.task'].search(
                    [('google_task', '=', task_data['id'])], limit=1)
                google_project = self.env.ref('odoo_google_tasks_integration.google_project')

                if not task_id:
                    # Convert date string to datetime object
                    date_obj = datetime.strptime(task_data['due'],
                                                 '%Y-%m-%dT%H:%M:%S.%fZ') if task_data.get(
                        'due') else False

                    # Create the task
                    task_id = self.env['project.task'].create({
                        'name': task_data['title'],
                        'date_deadline': date_obj,
                        'google_task': task_data['id'],
                        'is_imported': True,
                        'project_id': google_project.id
                    })

                # Store the task in the map for parent-child relationship handling
                task_map[task_data['id']] = task_id

            # Second pass: Assign parent tasks
            for task_data in tasks:
                parent_id = task_data.get('parent')
                if parent_id and parent_id in task_map:
                    child_task = task_map.get(task_data['id'])
                    parent_task = task_map.get(parent_id)

                    if child_task and parent_task:
                        child_task.parent_id = parent_task.id

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Successful'),
                    'type': 'success',
                    'message': _('Imported successfully!'),
                    'sticky': False,
                }
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Error'),
                'type': 'danger',
                'message': _('Failed to import tasks. Google API returned: %s') % response.text,
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
                'title': _('Successful'),
                'type': 'success',
                'message': 'Exported successfully!',
                'sticky': True,
            }
        }

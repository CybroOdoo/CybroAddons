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
from bs4 import BeautifulSoup
from datetime import datetime
from odoo import api, fields, models

TIMEOUT = 20


class ProjectTask(models.Model):
    """ Model for Project Task to add in google task """
    _inherit = 'project.task'

    is_add_in_gtask = fields.Boolean(string="Add In Google Task",
                                     help='Whether to add the task in Google'
                                          ' Task')
    google_task = fields.Char(string="Exported to Google Task",
                              help='ID of the task exported to Google Task')
    is_imported = fields.Boolean(string='Imported From Google Task',
                                 help='Whether the task is imported from '
                                      'Google Task')
    task_id = fields.Many2one('project.task', string='Task',
                              help='Select a task from the list.')

    @api.model_create_multi
    def create(self, vals_list):
        """Create method override to sync task with Google Task when created"""
        tasks = super().create(vals_list)
        for task in tasks:
            if task.is_add_in_gtask:
                task.action_sync_task_to_google()
        return tasks

    def write(self, vals):
        """Write method override to sync task with Google Task when updated"""
        res = super(ProjectTask, self).write(vals)
        if self.env.context.get('skip_gtask_sync'):
            return res
        sync_fields = ['name', 'description', 'date_deadline', 'is_add_in_gtask']
        if any(field in vals for field in sync_fields):
            for task in self:
                if task.is_add_in_gtask:
                    task.action_sync_task_to_google()
        return res

    def action_sync_task_to_google(self):
        """Sync the task to Google Task"""
        self = self.with_context(skip_gtask_sync=True)
        if not self.description:
            self.description = "New Task added to Google Task"
        self.is_add_in_gtask = True
        company_id = self.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data')
        url = "https://tasks.googleapis.com/tasks/v1/lists/@default/tasks"
        headers = {
            "Authorization": f"Bearer "
                             f"{company_id.hangout_company_access_token}",
            'Content-Type': 'application/json',
            "Accept": "application/json"
        }
        # Extract the plain text from the description using BeautifulSoup
        soup = BeautifulSoup(self.description, 'html.parser')
        note = soup.get_text()
        datetime_obj = fields.datetime.combine(
            self.date_deadline or fields.Date.today(), datetime.min.time())
        main_task_data = {
            'title': self.name,
            'due': datetime_obj.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'notes': note if self.description else None,
        }
        # Create or update the main task
        if self.google_task:
            main_task_url = f"https://tasks.googleapis.com/tasks/v1/lists/" \
                            f"@default/tasks/{self.google_task}"
            response = requests.patch(main_task_url, headers=headers,
                                      json=main_task_data, timeout=TIMEOUT)
        else:
            response = requests.post(url, headers=headers, json=main_task_data ,timeout=TIMEOUT)

        if response.status_code == 401:
            # Token might be expired, try to refresh and retry
            company_id.action_google_task_company_refresh_token()
            headers["Authorization"] = f"Bearer {company_id.hangout_company_access_token}"
            if self.google_task:
                response = requests.patch(main_task_url, headers=headers,
                                          json=main_task_data , timeout=TIMEOUT)
            else:
                response = requests.post(url, headers=headers, json=main_task_data,timeout=TIMEOUT)

        if response.status_code in [200, 201]:
            main_task_id = response.json().get('id')
            if self.google_task != main_task_id:
                self.google_task = main_task_id
                message = f'(Main task created/updated: {main_task_id})'
                self.message_post(body=message)
            # Update the corresponding Google task for the current task
            google_task = self.env['project.task'].search(
                [('task_id', '=', self.id)], limit=1)
            if google_task and google_task.google_task != main_task_id:
                google_task.google_task = main_task_id
            # Process subtasks
            subtasks = self.child_ids.with_context(skip_gtask_sync=True)
            for subtask in subtasks:
                subtask_data = {
                    'title': subtask.name,
                    'status': 'needsAction',
                }
                if subtask.google_task:
                    subtask_url = f"https://tasks.googleapis.com/tasks/v1/" \
                                  f"lists/@default/tasks/{subtask.google_task}"
                    response = requests.patch(subtask_url, headers=headers,
                                              json=subtask_data ,timeout=TIMEOUT)
                else:
                    response = requests.post(url, headers=headers,
                                             json=subtask_data ,timeout=TIMEOUT)
                if response.status_code == 200:
                    subtask_id = response.json().get('id')
                    if subtask.google_task != subtask_id:
                        subtask.google_task = subtask_id
                        message = f'(Subtask created/updated: {subtask_id})'
                        self.message_post(body=message)
                    # Move the subtask under the main task
                    move_url = f"https://tasks.googleapis.com/tasks/v1/lists/"\
                               f"@default/tasks/{subtask_id}/move"
                    move_data = {
                        'parent': main_task_id
                    }
                    response = requests.post(move_url, headers=headers,
                                                  json=move_data ,timeout=TIMEOUT)
        return response

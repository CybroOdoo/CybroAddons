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
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext, is_html_empty

_logger = logging.getLogger(__name__)

# Changing these on an exported task updates it in Google Tasks
SYNC_FIELDS = {'name', 'description', 'date_deadline', 'child_ids'}


class ProjectTask(models.Model):
    """Export project tasks and their subtasks to Google Tasks"""
    _inherit = 'project.task'

    is_add_in_gtask = fields.Boolean(string='Add In Google Task', copy=False,
                                     help='Whether the task is exported to '
                                          'Google Tasks')
    google_task = fields.Char(string='Google Task ID', copy=False,
                              help='ID of the task in Google Tasks')
    is_imported = fields.Boolean(string='Imported From Google Task',
                                 copy=False,
                                 help='Whether the task was imported from '
                                      'Google Tasks')

    @api.model_create_multi
    def create(self, vals_list):
        """Export the new tasks marked to be added in Google Tasks"""
        tasks = super().create(vals_list)
        tasks.filtered('is_add_in_gtask')._auto_sync_to_google()
        return tasks

    def write(self, vals):
        """Keep the exported tasks up to date in Google Tasks"""
        res = super().write(vals)
        if not self.env.context.get('skip_gtask_sync'):
            if vals.get('is_add_in_gtask'):
                self._auto_sync_to_google()
            elif SYNC_FIELDS & vals.keys():
                self.filtered('google_task')._auto_sync_to_google()
        return res

    def _get_google_credential(self):
        return self.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data',
        ).sudo()

    def _get_google_task_values(self):
        """Values of the task sent to Google Tasks"""
        self.ensure_one()
        values = {'title': self.name}
        if not is_html_empty(self.description):
            values['notes'] = html2plaintext(self.description)
        if self.date_deadline:
            # Google Tasks only keeps the date of the due time
            values['due'] = self.date_deadline.strftime('%Y-%m-%dT00:00:00Z')
        return values

    def _push_to_google(self, credential, parent_google_id=False):
        """Create or update the task in Google Tasks and return its ID"""
        self.ensure_one()
        values = self._get_google_task_values()
        response = None
        if self.google_task:
            response = credential._google_tasks_request(
                'PATCH', f'/{self.google_task}', json=values)
        if response is None or response.status_code == 404:
            # New task, or deleted in Google Tasks: create it again
            params = {'parent': parent_google_id} if parent_google_id else {}
            response = credential._google_tasks_request(
                'POST', json=values, params=params)
        if response.status_code != 200:
            raise UserError(self.env._(
                'Google Tasks refused the task "%(task)s": %(error)s',
                task=self.name, error=response.text))
        google_id = response.json().get('id')
        if self.google_task != google_id:
            self.with_context(skip_gtask_sync=True).google_task = google_id
            self.message_post(body=self.env._(
                'Exported to Google Tasks (ID %s).', google_id))
        return google_id

    def _sync_to_google(self):
        """Export the tasks and their subtasks to Google Tasks"""
        credential = self._get_google_credential()
        for task in self:
            google_id = task._push_to_google(credential)
            task.with_context(skip_gtask_sync=True).is_add_in_gtask = True
            for subtask in task.child_ids:
                subtask._push_to_google(credential, parent_google_id=google_id)

    def _sync_each_to_google(self):
        """Export the tasks one by one; return the errors by task"""
        errors = {}
        for task in self:
            try:
                with self.env.cr.savepoint():
                    task._sync_to_google()
            except UserError as error:
                errors[task] = str(error)
        return errors

    def _auto_sync_to_google(self):
        """Sync on save: log errors instead of blocking the save"""
        for task, error in self._sync_each_to_google().items():
            _logger.warning('Google Tasks sync failed for task %s: %s',
                            task.id, error)
            task.message_post(
                body=self.env._('Google Tasks sync failed: %s', error))

    def action_sync_task_to_google(self):
        """Export the selected tasks to Google Tasks"""
        errors = self._sync_each_to_google()
        if errors:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': self.env._('Export Failed'),
                    'message': '\n'.join(errors.values()),
                    'type': 'warning',
                    'sticky': True,
                },
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Export Successful'),
                'message': self.env._(
                    '%s task(s) exported to Google Tasks.', len(self)),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }

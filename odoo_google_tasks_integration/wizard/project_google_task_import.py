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
from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import plaintext2html


class ProjectGoogleTaskImport(models.TransientModel):
    """Wizard to import tasks from Google Tasks or export tasks to it"""
    _name = 'project.google.task.import'
    _description = 'Google Task Import'

    export_import_selection = fields.Selection([
        ('import', 'Import from Google Task'),
        ('export', 'Export to Google Task')],
        string='Select Action', default='import', required=True,
        help='Import the tasks from Google Tasks, or export project tasks '
             'to Google Tasks')
    project_id = fields.Many2one(
        'project.project',
        help='Project of the imported tasks. Without a project, they are '
             'created as your private tasks and Google subtasks are '
             'imported as separate tasks.')
    task_ids = fields.Many2many('project.task',
                                string='Tasks to Export',
                                help='Tasks to export to Google Tasks')

    def _fetch_google_tasks(self, credential):
        """All the tasks of the default Google Tasks list"""
        items, params = [], {'maxResults': 100}
        while True:
            response = credential._google_tasks_request('GET', params=params)
            if response.status_code != 200:
                raise UserError(self.env._(
                    'Google Tasks returned an error: %s', response.text))
            result = response.json()
            items += result.get('items', [])
            if not result.get('nextPageToken'):
                return items
            params['pageToken'] = result['nextPageToken']

    def action_import_tasks(self):
        """Create the Google tasks that are not in Odoo yet"""
        Task = self.env['project.task'].with_context(skip_gtask_sync=True)
        credential = Task._get_google_credential()
        google_tasks = self._fetch_google_tasks(credential)
        existing = Task.search([
            ('google_task', 'in', [item['id'] for item in google_tasks])])
        tasks_by_google_id = {task.google_task: task for task in existing}
        new_items = [item for item in google_tasks
                     if item['id'] not in tasks_by_google_id]
        new_tasks = Task.create([{
            'name': item.get('title') or self.env._('Untitled'),
            'description': plaintext2html(item['notes'])
            if item.get('notes') else False,
            'date_deadline': item['due'][:10] if item.get('due') else False,
            'google_task': item['id'],
            'is_imported': True,
            'project_id': self.project_id.id,
            # Tasks without a project are only visible to their assignees
            'user_ids': [] if self.project_id else [self.env.uid],
        } for item in new_items])
        tasks_by_google_id.update(zip(
            [item['id'] for item in new_items], new_tasks))
        # Keep the Google subtasks under their parent task (private tasks
        # cannot have a parent task)
        for item, task in zip(new_items, new_tasks):
            parent = tasks_by_google_id.get(item.get('parent'))
            if parent and task.project_id and parent.project_id:
                task.parent_id = parent
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Import Successful'),
                'type': 'success',
                'message': self.env._(
                    'Imported %s tasks from Google Task.', len(new_tasks)),
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_export_task(self):
        """Export the selected tasks to Google Tasks"""
        if not self.task_ids:
            raise UserError(self.env._('Select the tasks to export.'))
        action = self.task_ids.action_sync_task_to_google()
        if action['params']['type'] == 'success':
            action['params']['next'] = {
                'type': 'ir.actions.act_window_close'}
        return action

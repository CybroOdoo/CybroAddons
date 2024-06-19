# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sayanth M K(<https://www.cybrosys.com>)
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
from .todoist_api_python.api import TodoistAPI
from odoo import fields, models, _
from odoo.exceptions import MissingError


def _get_todoist_projects_tasks(token, project=False):
    """Fetch Projects and Tasks from API"""
    try:
        return TodoistAPI(
            token).get_projects() if project else TodoistAPI(token).get_tasks()
    except Exception as error:
        return error


class ResUsers(models.Model):
    """Extends res_users model to integrate Todoist functionality."""
    _inherit = 'res.users'

    todoist_token = fields.Char(string='Todoist Token',
                                help='todoist auth token to retrieve data'
                                     ' from todoist',
                                copy=False)

    def _fetch_token(self):
        """Method to fetch a token from user"""
        if self.todoist_token:
            return self.todoist_token
        raise MissingError('Token not found!')

    def _add_all_projects(self):
        """Add all projects or Write projects with updated data from API"""
        for project in _get_todoist_projects_tasks(self._fetch_token(),
                                                   project=True):
            vals = {'todo_project': str(project.id), 'name': project.name}
            exist = self.env['project.project'].sudo().search(
                [('todo_project', '=', vals['todo_project'])],
                limit=1)
            exist.write(vals) if exist else self.env[
                'project.project'].sudo().create(vals)

    def _add_task_tags(self, tags):
        """Add all tags or Write tags with updated data from API"""
        TagModel = self.env['project.tags']
        existing_tags = {tag.name: tag for tag in
                         TagModel.sudo().search([('name', 'in', tags)])}
        created_tags = TagModel.sudo().create(
            [{'name': tag} for tag in tags if tag not in existing_tags])
        existing_tags.update({tag.name: tag for tag in created_tags})
        return [existing_tags[tag].id for tag in tags]

    def _add_all_tasks(self):
        """Add all tasks or Write tasks with updated data from API"""
        ProjectModel = self.env['project.project']
        TaskModel = self.env['project.task']
        for task in _get_todoist_projects_tasks(self._fetch_token(),
                                                project=False):
            task_vals = {
                'project_id': ProjectModel.sudo().search(
                    [('todo_project', '=', str(task.project_id))], limit=1).id,
                'name': task.content,
                'todo_task': str(task.id),
                'date_deadline': task.due.date if task.due else False,
                'tag_ids': [(6, 0, self._add_task_tags(task.labels))],
                'description': task.description if task.description else False,
            }
            existing_task = TaskModel.sudo().search(
                [('todo_task', '=', task_vals['todo_task'])], limit=1)
            existing_task.write(
                task_vals) if existing_task else TaskModel.sudo().create(
                task_vals)

    def action_sync_todoist_with_odoo(self):
        """Sync the Todoist with odoo"""
        self._add_all_projects()
        self._add_all_tasks()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': (_("Successfully Synchronized Data!")),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

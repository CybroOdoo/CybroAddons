# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (<https://www.cybrosys.com>)
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
import requests

from odoo import Command, fields, models
from odoo.exceptions import AccessError, MissingError, UserError

TODOIST_API_URL = 'https://api.todoist.com/api/v1/'
TODOIST_TIMEOUT = 30
NO_SECTION = 'no_section'


def _get_todoist_data(env, token, endpoint):
    """Fetch all records of an endpoint (projects, sections, tasks) from
    the Todoist API, page by page"""
    url = TODOIST_API_URL + endpoint
    headers = {'Authorization': f'Bearer {token}'}
    params = {'limit': 200}
    records = []
    while True:
        try:
            response = requests.get(url, headers=headers, params=params,
                                    timeout=TODOIST_TIMEOUT)
        except requests.exceptions.RequestException as error:
            raise UserError(env._('Could not connect to Todoist: %(error)s',
                                  error=error)) from error
        if response.status_code in (401, 403):
            raise UserError(env._('The Todoist token is invalid or expired. '
                                  'Copy the API token again from Todoist '
                                  'Settings > Integrations > Developer.'))
        if not response.ok:
            raise UserError(env._('Todoist returned an error (%(code)s): '
                                  '%(reason)s', code=response.status_code,
                                  reason=response.text[:200]))
        data = response.json()
        records += data.get('results', [])
        if not data.get('next_cursor'):
            return records
        params['cursor'] = data['next_cursor']


class ResUsers(models.Model):
    """Extends res_users model to integrate Todoist functionality."""
    _inherit = 'res.users'

    todoist_token = fields.Char(
        groups='base.group_system',
        copy=False,
        help='API token from Todoist Settings > Integrations > Developer.',
    )

    @property
    def SELF_READABLE_FIELDS(self):
        """Users read their own token in My Preferences."""
        return super().SELF_READABLE_FIELDS + ['todoist_token']

    @property
    def SELF_WRITEABLE_FIELDS(self):
        """Users save their own token in My Preferences."""
        return super().SELF_WRITEABLE_FIELDS + ['todoist_token']

    def _fetch_token(self):
        """Method to fetch a token from user"""
        self.ensure_one()
        token = self.sudo().todoist_token
        if token:
            return token
        raise MissingError(self.env._('Token not found!'))

    def _get_todoist_records(self, endpoint):
        """Fetch the records of an endpoint with the token of this user."""
        return _get_todoist_data(self.env, self._fetch_token(), endpoint)

    def _add_all_projects(self):
        """Add all projects or Write projects with updated data from API"""
        ProjectModel = self.env['project.project'].sudo().with_context(
            active_test=False)
        projects = self._get_todoist_records('projects')
        existing = {record.todo_project: record for record in
                    ProjectModel.search([('todo_project', 'in', [
                        str(project['id']) for project in projects])])}
        for project in projects:
            todo_id = str(project['id'])
            vals = {'todo_project': todo_id, 'name': project['name']}
            if todo_id in existing:
                existing[todo_id].write(vals)
            else:
                ProjectModel.create(vals)

    def _get_synced_projects(self, todoist_records):
        """Return the synced projects of the records, by Todoist id."""
        projects = self.env['project.project'].sudo().with_context(
            active_test=False).search([('todo_project', 'in', [
                str(record['project_id']) for record in todoist_records])])
        return {project.todo_project: project for project in projects}

    def _add_all_sections(self):
        """Add the sections of the Todoist projects as stages of the
        synced projects, in the Todoist order"""
        StageModel = self.env['project.task.type'].sudo()
        sections = [section for section
                    in self._get_todoist_records('sections')
                    if not section.get('is_archived')]
        projects = self._get_synced_projects(sections)
        stages = self._get_synced_stages(
            [str(section['id']) for section in sections])
        for section in sections:
            todo_id = str(section['id'])
            project = projects.get(str(section['project_id']))
            vals = {'todo_section': todo_id,
                    'name': section['name'],
                    'sequence': section.get('section_order', 1)}
            if project:
                vals['project_ids'] = [Command.link(project.id)]
            if todo_id in stages:
                stages[todo_id].write(vals)
            else:
                StageModel.create(vals)

    def _get_synced_stages(self, section_ids):
        """Return the stages of the Todoist sections, by Todoist id."""
        stages = self.env['project.task.type'].sudo().with_context(
            active_test=False).search([('todo_section', 'in', section_ids)])
        return {stage.todo_section: stage for stage in stages}

    def _get_task_stage(self, task, project, stages):
        """Stage of a Todoist task: its section, or the No Section stage
        (like the Todoist board) for tasks outside of any section"""
        if not project:
            return self.env['project.task.type']
        section_id = str(task.get('section_id') or NO_SECTION)
        stage = stages.get(section_id) or stages.get(NO_SECTION)
        if not stage:
            stage = self.env['project.task.type'].sudo().create({
                'todo_section': NO_SECTION,
                'name': self.env._('No Section'),
                'sequence': 0,
            })
            stages[NO_SECTION] = stage
        if (stage.todo_section == NO_SECTION
                and project not in stage.project_ids):
            stage.project_ids = [Command.link(project.id)]
        return stage

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
        TaskModel = self.env['project.task'].sudo().with_context(
            active_test=False)
        tasks = self._get_todoist_records('tasks')
        projects = self._get_synced_projects(tasks)
        stages = self._get_synced_stages(
            [str(task['section_id']) for task in tasks
             if task.get('section_id')] + [NO_SECTION])
        existing = {record.todo_task: record for record in
                    TaskModel.search([('todo_task', 'in', [
                        str(task['id']) for task in tasks])])}
        synced_tasks = {}
        for task in tasks:
            due = task.get('due')
            todo_id = str(task['id'])
            project = projects.get(str(task['project_id']),
                                   self.env['project.project'])
            task_vals = {
                'project_id': project.id,
                'stage_id': self._get_task_stage(task, project, stages).id,
                'name': task['content'],
                'todo_task': todo_id,
                # due date is 'YYYY-MM-DD', or a date and time for timed tasks
                'date_deadline': due['date'][:10] if due else False,
                'tag_ids': [
                    Command.set(self._add_task_tags(task.get('labels', [])))],
                'description': task.get('description') or False,
            }
            record = existing.get(todo_id)
            if record:
                record.write(task_vals)
            else:
                record = TaskModel.create(task_vals)
            synced_tasks[todo_id] = (record, task.get('parent_id'))
        self._link_sub_tasks(synced_tasks)

    def _link_sub_tasks(self, synced_tasks):
        """Set the parent task of the Todoist sub-tasks, once all the tasks
        exist (a sub-task can come before its parent in the API data)"""
        for record, parent_id in synced_tasks.values():
            parent = synced_tasks[str(parent_id)][0] if str(
                parent_id) in synced_tasks else self.env['project.task']
            if record.parent_id != parent:
                record.parent_id = parent

    def action_sync_todoist_with_odoo(self):
        """Sync the Todoist with odoo"""
        self.ensure_one()
        if self != self.env.user:
            raise AccessError(self.env._(
                'You can only sync Todoist with your own token.'))
        if not self.env.user.has_group('project.group_project_user'):
            raise AccessError(self.env._(
                'Only Project users can sync Todoist.'))
        self._add_all_projects()
        self._add_all_sections()
        self._add_all_tasks()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': self.env._("Successfully Synchronized Data!"),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

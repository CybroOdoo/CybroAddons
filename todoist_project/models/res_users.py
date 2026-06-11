# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import _, fields, models
from odoo.exceptions import MissingError, UserError

TODOIST_API_BASE = "https://api.todoist.com/api/v1"
TODOIST_REQUEST_TIMEOUT = 30
TODOIST_RETRYABLE_STATUS_CODES = {429, 502, 503, 504}


def _todoist_get(url, headers, retries=3):
    """Fetch a Todoist API response with a small retry budget."""
    last_error = None

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers,
                                    timeout=TODOIST_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as error:
            status_code = getattr(error.response, 'status_code', None)
            if status_code not in TODOIST_RETRYABLE_STATUS_CODES or attempt == retries - 1:
                raise
            last_error = error
        except requests.exceptions.RequestException as error:
            if attempt == retries - 1:
                raise
            last_error = error

    if last_error:
        raise last_error


def _get_todoist_projects_tasks(token, project=False):
    """Fetch Projects and Tasks from Todoist API v1"""
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = "projects" if project else "tasks"
    url = f"{TODOIST_API_BASE}/{endpoint}"
    all_results = []

    try:
        while url:
            response = _todoist_get(url, headers)
            data = response.json()

            if isinstance(data, dict):
                all_results.extend(data.get('results', []))
                next_cursor = data.get('next_cursor')
                url = (
                    f"{TODOIST_API_BASE}/{endpoint}?cursor={next_cursor}"
                    if next_cursor else None
                )
            else:
                return data

        return all_results

    except requests.exceptions.HTTPError as error:
        status_code = getattr(error.response, 'status_code', None)
        if status_code in TODOIST_RETRYABLE_STATUS_CODES:
            raise UserError(_(
                "Todoist API is temporarily unavailable. "
                "Please try syncing again in a few minutes."
            ))
        if status_code in (401, 403):
            raise UserError(_(
                "Todoist authorization failed. Check that the token in Odoo "
                "is valid and belongs to the correct Todoist account."
            ))
        raise UserError(_(f"Todoist API Error: {error}"))
    except Exception as error:
        raise UserError(_(f"Failed to connect to Todoist: {error}"))


def _get_todoist_sections(token, project_id):
    """Fetch all Sections for a given Todoist project ID (API v1)."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{TODOIST_API_BASE}/sections?project_id={project_id}"
    all_results = []

    try:
        while url:
            response = _todoist_get(url, headers)
            data = response.json()

            if isinstance(data, dict):
                all_results.extend(data.get('results', []))
                next_cursor = data.get('next_cursor')
                url = (
                    f"{TODOIST_API_BASE}/sections"
                    f"?project_id={project_id}&cursor={next_cursor}"
                    if next_cursor else None
                )
            else:
                return data

        return all_results

    except requests.exceptions.HTTPError as error:
        status_code = getattr(error.response, 'status_code', None)
        if status_code in TODOIST_RETRYABLE_STATUS_CODES:
            raise UserError(_(
                "Todoist API is temporarily unavailable while fetching "
                "sections. Please try again later."
            ))
        if status_code in (401, 403):
            raise UserError(_(
                "Todoist authorization failed while fetching sections. "
                "Check the token stored in Odoo."
            ))
        raise UserError(_(f"Todoist API Error (sections): {error}"))
    except Exception as error:
        raise UserError(_(f"Failed to fetch Todoist sections: {error}"))


class ResUsers(models.Model):
    """Extends res_users model to integrate Todoist functionality."""
    _inherit = 'res.users'

    todoist_token = fields.Char(
        string='Todoist Token',
        help='Todoist auth token to retrieve data from Todoist',
        copy=False,
    )

    def _fetch_token(self):
        """Return the stored Todoist token or raise if missing."""
        if self.todoist_token:
            return self.todoist_token
        raise MissingError('Token not found!')

    def _add_all_projects(self, todoist_projects, project_cache=None):
        """Create or update Odoo projects from Todoist projects."""
        project_cache = project_cache if project_cache is not None else {}
        for project in todoist_projects:
            vals = {
                'todo_project': str(project['id']),
                'name': project['name'],
            }
            exist = self.env['project.project'].sudo().search(
                [('todo_project', '=', vals['todo_project'])], limit=1)
            if exist:
                exist.write(vals)
                project_cache[vals['todo_project']] = exist
            else:
                project_cache[vals['todo_project']] = self.env[
                    'project.project'].sudo().create(vals)
        return project_cache

    def _get_or_create_stage(self, section_id, section_name, project_id,
                             stage_cache=None):
        """
        Return the Odoo project.task.type that matches the given Todoist
        section_id (scoped to the project), creating it if necessary.

        :param section_id:   Todoist section ID string  (or None / '')
        :param section_name: Human-readable name for the stage
        :param project_id:   Odoo project.project record ID (int)
        :return:             project.task.type record
        """
        stage_cache = stage_cache if stage_cache is not None else {}
        StageModel = self.env['project.task.type'].sudo()

        if section_id:
            cache_key = str(section_id)
            stage = stage_cache.get(cache_key)
            if not stage:
                stage = StageModel.search(
                    [('todo_stage', '=', cache_key)], limit=1)
                if stage:
                    stage_cache[cache_key] = stage
            if stage:
                # Make sure this project is linked to the stage
                if project_id not in stage.project_ids.ids:
                    stage.write(
                        {'project_ids': [(4, project_id)]})
                stage_cache[cache_key] = stage
                return stage

            # Create a new stage mapped to this Todoist section
            stage = StageModel.create({
                'name': section_name,
                'todo_stage': cache_key,
                'project_ids': [(4, project_id)],
            })
            stage_cache[cache_key] = stage
            return stage

        # No section → fall back to a generic "To Do" stage for the project
        cache_key = f"{project_id}:todo"
        fallback = stage_cache.get(cache_key)
        if not fallback:
            fallback = StageModel.search(
                [('name', '=', 'To Do'),
                 ('project_ids', 'in', [project_id])], limit=1)
            if fallback:
                stage_cache[cache_key] = fallback
        if not fallback:
            fallback = StageModel.create({
                'name': 'To Do',
                'project_ids': [(4, project_id)],
            })
        stage_cache[cache_key] = fallback
        return fallback

    def _add_all_sections(self, todoist_projects, project_cache=None,
                          stage_cache=None):
        """
        Pre-sync all Todoist sections as Odoo stages so that
        _add_all_tasks can look them up quickly.

        :param todoist_projects: list of Todoist project dicts
        """
        project_cache = project_cache if project_cache is not None else {}
        stage_cache = stage_cache if stage_cache is not None else {}
        token = self._fetch_token()

        for project in todoist_projects:
            odoo_project = project_cache.get(str(project['id']))
            if not odoo_project:
                continue

            sections = _get_todoist_sections(token, project['id'])
            for section in sections:
                self._get_or_create_stage(
                    section_id=str(section['id']),
                    section_name=section['name'],
                    project_id=odoo_project.id,
                    stage_cache=stage_cache,
                )

    def _add_task_tags(self, tags, tag_cache=None):
        """Create or reuse project.tags records for the given label names."""
        tag_cache = tag_cache if tag_cache is not None else {}
        TagModel = self.env['project.tags'].sudo()
        missing_tags = [tag for tag in tags if tag not in tag_cache]
        if missing_tags:
            existing_tags = {
                tag.name: tag for tag in
                TagModel.search([('name', 'in', missing_tags)])
            }
            created_tags = TagModel.create(
                [{'name': tag} for tag in missing_tags
                 if tag not in existing_tags])
            existing_tags.update({tag.name: tag for tag in created_tags})
            tag_cache.update(existing_tags)
        return [tag_cache[tag].id for tag in tags if tag in tag_cache]

    def _add_all_tasks(self, todoist_projects, project_cache=None,
                       stage_cache=None, tag_cache=None, task_cache=None):
        """Create or update Odoo tasks from Todoist tasks, including stages."""
        TaskModel = self.env['project.task'].sudo()
        project_cache = project_cache if project_cache is not None else {}
        stage_cache = stage_cache if stage_cache is not None else {}
        tag_cache = tag_cache if tag_cache is not None else {}
        task_cache = task_cache if task_cache is not None else {}
        token = self._fetch_token()

        todoist_tasks = _get_todoist_projects_tasks(token, project=False)

        for task in todoist_tasks:
            due = task.get('due')
            todoist_project_id = str(task.get('project_id', ''))
            todoist_section_id = task.get('section_id')  # may be None

            odoo_project = project_cache.get(todoist_project_id)

            # ------------------------------------------------------------------
            # Resolve stage
            # ------------------------------------------------------------------
            stage = False
            if odoo_project:
                if todoist_section_id:
                    # Look up the pre-synced stage by Todoist section ID
                    stage = stage_cache.get(str(todoist_section_id))
                    if not stage:
                        # Fallback: create on the fly (shouldn't normally happen
                        # after _add_all_sections ran, but safe-guard anyway)
                        stage = self._get_or_create_stage(
                            section_id=str(todoist_section_id),
                            section_name=f'Section {todoist_section_id}',
                            project_id=odoo_project.id,
                            stage_cache=stage_cache,
                        )
                else:
                    stage = self._get_or_create_stage(
                        section_id=None,
                        section_name='To Do',
                        project_id=odoo_project.id,
                        stage_cache=stage_cache,
                    )

            task_vals = {
                'project_id': odoo_project.id if odoo_project else False,
                'name': task.get('content'),
                'todo_task': str(task['id']),
                'date_deadline': due.get('date') if due else False,
                'tag_ids': [(6, 0, self._add_task_tags(
                    task.get('labels', []), tag_cache=tag_cache))],
                'description': task.get('description', '') or False,
            }
            if stage:
                task_vals['stage_id'] = stage.id

            existing_task = task_cache.get(task_vals['todo_task'])
            if existing_task is None:
                existing_task = TaskModel.search(
                    [('todo_task', '=', task_vals['todo_task'])], limit=1)
                if existing_task:
                    task_cache[task_vals['todo_task']] = existing_task
            if existing_task:
                existing_task.write(task_vals)
                task_cache[task_vals['todo_task']] = existing_task
            else:
                task_cache[task_vals['todo_task']] = TaskModel.create(task_vals)

        # ------------------------------------------------------------------
        # Second pass: wire up parent–child relationships
        # ------------------------------------------------------------------
        for task in todoist_tasks:
            parent_id = task.get('parent_id')
            if parent_id:
                parent_task = task_cache.get(str(parent_id))
                child_task = task_cache.get(str(task['id']))
                if parent_task and child_task:
                    child_task.write({'parent_id': parent_task.id})

    def action_sync_todoist_with_odoo(self):
        """Sync Todoist projects, sections (→ stages), and tasks into Odoo."""
        todoist_projects = _get_todoist_projects_tasks(
            self._fetch_token(), project=True)
        project_cache = {}
        stage_cache = {}
        tag_cache = {}
        task_cache = {}

        # 1. Sync projects first
        project_cache = self._add_all_projects(
            todoist_projects, project_cache=project_cache)

        # 2. Sync sections as Odoo stages (must come before tasks)
        self._add_all_sections(
            todoist_projects,
            project_cache=project_cache,
            stage_cache=stage_cache,
        )

        # 3. Sync tasks with stage_id populated
        self._add_all_tasks(
            todoist_projects,
            project_cache=project_cache,
            stage_cache=stage_cache,
            tag_cache=tag_cache,
            task_cache=task_cache,
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _("Successfully Synchronized Data!"),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

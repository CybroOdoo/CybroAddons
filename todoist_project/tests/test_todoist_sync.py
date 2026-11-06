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
from datetime import date
from unittest.mock import MagicMock, patch

import requests

from odoo import fields
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase

from odoo.addons.todoist_project.models.res_users import _get_todoist_data

FETCH_PATCH_TARGET = (
    'odoo.addons.todoist_project.models.res_users._get_todoist_data'
)
REQUESTS_PATCH_TARGET = (
    'odoo.addons.todoist_project.models.res_users.requests.get'
)


def _make_project(id_, name):
    return {'id': id_, 'name': name}


def _make_section(id_, project_id, name, order=1, archived=False):
    return {'id': id_, 'project_id': project_id, 'name': name,
            'section_order': order, 'is_archived': archived}


def _make_task(id_, project_id, content, due_date=None, labels=None,
               description=None, section_id=None, parent_id=None):
    """A task as returned by the Todoist API v1"""
    return {
        'id': id_,
        'parent_id': parent_id,
        'project_id': project_id,
        'section_id': section_id,
        'content': content,
        'due': {'date': due_date} if due_date else None,
        'labels': labels or [],
        'description': description or '',
    }


def _response(status_code=200, results=None, next_cursor=None, text=''):
    response = MagicMock(status_code=status_code, ok=status_code < 400,
                         text=text)
    response.json.return_value = {'results': results or [],
                                  'next_cursor': next_cursor}
    return response


class TestFetchToken(TransactionCase):
    """Test the token guard used before every Todoist API call."""

    def setUp(self):
        super().setUp()
        self.user = self.env.user

    def test_fetch_token_returns_the_stored_token(self):
        self.user.todoist_token = 'my-secret-token'

        self.assertEqual(self.user._fetch_token(), 'my-secret-token')

    def test_fetch_token_raises_when_no_token_is_set(self):
        self.user.todoist_token = False

        with self.assertRaises(MissingError):
            self.user._fetch_token()


class TestAddTaskTags(TransactionCase):
    """Test the tag reuse/creation helper."""

    def setUp(self):
        super().setUp()
        self.user = self.env.user

    def test_reuses_existing_tags_and_creates_missing_ones(self):
        existing_tag = self.env['project.tags'].create({'name': 'urgent'})

        tag_ids = self.user._add_task_tags(['urgent', 'design'])

        self.assertEqual(len(tag_ids), 2)
        self.assertIn(existing_tag.id, tag_ids)
        new_tag = self.env['project.tags'].search([('name', '=', 'design')])
        self.assertEqual(len(new_tag), 1)
        self.assertIn(new_tag.id, tag_ids)
        # the existing tag must not have been duplicated
        self.assertEqual(
            self.env['project.tags'].search_count([('name', '=', 'urgent')]),
            1,
        )

    def test_empty_tag_list_returns_empty_list(self):
        self.assertEqual(self.user._add_task_tags([]), [])


class TestAddAllProjects(TransactionCase):
    """Test syncing Todoist projects into project.project."""

    def setUp(self):
        super().setUp()
        self.user = self.env.user
        self.user.todoist_token = 'tok'

    @patch(FETCH_PATCH_TARGET)
    def test_creates_a_new_project_for_each_todoist_project(self, mock_fetch):
        mock_fetch.return_value = [_make_project('6Jf8VQXxpwv56VQ7',
                                                 'Marketing')]

        self.user._add_all_projects()

        project = self.env['project.project'].search(
            [('todo_project', '=', '6Jf8VQXxpwv56VQ7')])
        self.assertEqual(len(project), 1)
        self.assertEqual(project.name, 'Marketing')

    @patch(FETCH_PATCH_TARGET)
    def test_updates_an_existing_project_instead_of_duplicating(
            self, mock_fetch):
        existing = self.env['project.project'].create(
            {'name': 'Old Name', 'todo_project': '111'})
        mock_fetch.return_value = [_make_project(111, 'New Name')]

        self.user._add_all_projects()

        self.assertEqual(existing.name, 'New Name')
        self.assertEqual(
            self.env['project.project'].search_count(
                [('todo_project', '=', '111')]),
            1,
        )

    @patch(FETCH_PATCH_TARGET)
    def test_raises_when_token_is_missing(self, mock_fetch):
        self.user.todoist_token = False

        with self.assertRaises(MissingError):
            self.user._add_all_projects()
        mock_fetch.assert_not_called()


class TestAddAllTasks(TransactionCase):
    """Test syncing Todoist tasks into project.task."""

    def setUp(self):
        super().setUp()
        self.user = self.env.user
        self.user.todoist_token = 'tok'
        self.project = self.env['project.project'].create(
            {'name': 'Marketing', 'todo_project': '111'})

    @patch(FETCH_PATCH_TARGET)
    def test_creates_a_new_task_with_project_deadline_and_tags(
            self, mock_fetch):
        mock_fetch.return_value = [_make_task(
            555, 111, 'Design banner',
            due_date='2026-09-01',
            labels=['urgent', 'design'],
            description='Needs the new logo',
        )]

        self.user._add_all_tasks()

        task = self.env['project.task'].search([('todo_task', '=', '555')])
        self.assertEqual(len(task), 1)
        self.assertEqual(task.name, 'Design banner')
        self.assertEqual(task.project_id, self.project)
        self.assertEqual(
            fields.Date.to_date(task.date_deadline), date(2026, 9, 1))
        self.assertIn('Needs the new logo', task.description or '')
        self.assertEqual(
            set(task.tag_ids.mapped('name')), {'urgent', 'design'})

    @patch(FETCH_PATCH_TARGET)
    def test_updates_an_existing_task_instead_of_duplicating(
            self, mock_fetch):
        existing_task = self.env['project.task'].create({
            'name': 'Old name',
            'todo_task': '555',
            'project_id': self.project.id,
        })
        mock_fetch.return_value = [
            _make_task(555, 111, 'New name', labels=[])]

        self.user._add_all_tasks()

        self.assertEqual(existing_task.name, 'New name')
        self.assertEqual(
            self.env['project.task'].search_count(
                [('todo_task', '=', '555')]),
            1,
        )

    @patch(FETCH_PATCH_TARGET)
    def test_missing_due_date_and_description_are_stored_as_falsy(
            self, mock_fetch):
        mock_fetch.return_value = [_make_task(
            555, 111, 'No due date', due_date=None,
            description=None, labels=[],
        )]

        self.user._add_all_tasks()

        task = self.env['project.task'].search([('todo_task', '=', '555')])
        self.assertFalse(task.date_deadline)
        self.assertFalse(task.description)

    @patch(FETCH_PATCH_TARGET)
    def test_timed_due_date_keeps_the_day(self, mock_fetch):
        mock_fetch.return_value = [_make_task(
            557, 111, 'Call client', due_date='2026-09-01T12:00:00')]

        self.user._add_all_tasks()

        task = self.env['project.task'].search([('todo_task', '=', '557')])
        self.assertEqual(
            fields.Date.to_date(task.date_deadline), date(2026, 9, 1))

    @patch(FETCH_PATCH_TARGET)
    def test_task_for_unknown_project_is_created_without_a_project(
            self, mock_fetch):
        mock_fetch.return_value = [
            _make_task(556, 999, 'Orphan task', labels=[])]

        self.user._add_all_tasks()

        task = self.env['project.task'].search([('todo_task', '=', '556')])
        self.assertEqual(len(task), 1)
        self.assertFalse(task.project_id)


class TestSectionsAndStages(TransactionCase):
    """Test syncing Todoist sections into project stages, so synced tasks
    show in the right kanban column instead of 'None'."""

    def setUp(self):
        super().setUp()
        self.user = self.env.user
        self.user.todoist_token = 'tok'
        self.project = self.env['project.project'].create(
            {'name': 'Marketing', 'todo_project': '111'})

    def _stage(self, section_id):
        return self.env['project.task.type'].search(
            [('todo_section', '=', section_id)])

    @patch(FETCH_PATCH_TARGET)
    def test_sections_become_ordered_stages_of_the_project(self, mock_fetch):
        mock_fetch.return_value = [
            _make_section('s2', '111', 'Doing', order=2),
            _make_section('s1', '111', 'Backlog', order=1),
            _make_section('s3', '111', 'Old', order=3, archived=True),
        ]

        self.user._add_all_sections()

        self.assertEqual(self.project.type_ids.sorted().mapped('name'),
                         ['Backlog', 'Doing'])
        self.assertFalse(self._stage('s3'))

    @patch(FETCH_PATCH_TARGET)
    def test_resync_renames_the_stage_instead_of_duplicating(
            self, mock_fetch):
        mock_fetch.return_value = [_make_section('s1', '111', 'Backlog')]
        self.user._add_all_sections()
        mock_fetch.return_value = [_make_section('s1', '111', 'Ideas')]

        self.user._add_all_sections()

        self.assertEqual(len(self._stage('s1')), 1)
        self.assertEqual(self._stage('s1').name, 'Ideas')

    @patch(FETCH_PATCH_TARGET)
    def test_task_goes_to_the_stage_of_its_section(self, mock_fetch):
        mock_fetch.return_value = [_make_section('s1', '111', 'Backlog')]
        self.user._add_all_sections()
        mock_fetch.return_value = [
            _make_task('t1', '111', 'In section', section_id='s1')]

        self.user._add_all_tasks()

        task = self.env['project.task'].search([('todo_task', '=', 't1')])
        self.assertEqual(task.stage_id, self._stage('s1'))

    @patch(FETCH_PATCH_TARGET)
    def test_task_without_section_goes_to_no_section_stage(self, mock_fetch):
        mock_fetch.return_value = [_make_task('t1', '111', 'Loose task')]

        self.user._add_all_tasks()

        task = self.env['project.task'].search([('todo_task', '=', 't1')])
        self.assertEqual(task.stage_id.name, 'No Section')
        self.assertIn(self.project, task.stage_id.project_ids)

    @patch(FETCH_PATCH_TARGET)
    def test_task_moved_to_another_section_changes_stage(self, mock_fetch):
        mock_fetch.return_value = [
            _make_section('s1', '111', 'Backlog', order=1),
            _make_section('s2', '111', 'Doing', order=2),
        ]
        self.user._add_all_sections()
        mock_fetch.return_value = [
            _make_task('t1', '111', 'Moving', section_id='s1')]
        self.user._add_all_tasks()
        mock_fetch.return_value = [
            _make_task('t1', '111', 'Moving', section_id='s2')]

        self.user._add_all_tasks()

        task = self.env['project.task'].search([('todo_task', '=', 't1')])
        self.assertEqual(task.stage_id, self._stage('s2'))

    @patch(FETCH_PATCH_TARGET)
    def test_task_without_project_has_no_stage(self, mock_fetch):
        mock_fetch.return_value = [_make_task('t1', '999', 'Orphan')]

        self.user._add_all_tasks()

        task = self.env['project.task'].search([('todo_task', '=', 't1')])
        self.assertFalse(task.stage_id)


class TestSubTasks(TransactionCase):
    """Test that Todoist sub-tasks become Odoo sub-tasks."""

    def setUp(self):
        super().setUp()
        self.user = self.env.user
        self.user.todoist_token = 'tok'
        self.project = self.env['project.project'].create(
            {'name': 'Marketing', 'todo_project': '111'})

    def _task(self, todo_id):
        return self.env['project.task'].search([('todo_task', '=', todo_id)])

    @patch(FETCH_PATCH_TARGET)
    def test_sub_task_is_linked_even_before_its_parent(self, mock_fetch):
        mock_fetch.return_value = [
            _make_task('child', '111', 'Child', parent_id='parent'),
            _make_task('parent', '111', 'Parent'),
        ]

        self.user._add_all_tasks()

        child, parent = self._task('child'), self._task('parent')
        self.assertEqual(child.parent_id, parent)
        self.assertEqual(parent.child_ids, child)
        self.assertFalse(parent.parent_id)
        # shown under its parent, not as its own card in the project
        self.assertEqual(child.project_id, self.project)
        self.assertFalse(child.display_in_project)

    @patch(FETCH_PATCH_TARGET)
    def test_sub_task_moved_out_of_its_parent_is_unlinked(self, mock_fetch):
        mock_fetch.return_value = [
            _make_task('parent', '111', 'Parent'),
            _make_task('child', '111', 'Child', parent_id='parent'),
        ]
        self.user._add_all_tasks()
        mock_fetch.return_value = [
            _make_task('parent', '111', 'Parent'),
            _make_task('child', '111', 'Child'),
        ]

        self.user._add_all_tasks()

        self.assertFalse(self._task('child').parent_id)
        self.assertTrue(self._task('child').display_in_project)


class TestActionSyncTodoistWithOdoo(TransactionCase):
    """Test the public sync action and its returned notification."""

    def setUp(self):
        super().setUp()
        self.user = self.env.user
        self.user.todoist_token = 'tok'

    @patch(
        'odoo.addons.todoist_project.models.res_users.ResUsers'
        '._add_all_tasks'
    )
    @patch(
        'odoo.addons.todoist_project.models.res_users.ResUsers'
        '._add_all_sections'
    )
    @patch(
        'odoo.addons.todoist_project.models.res_users.ResUsers'
        '._add_all_projects'
    )
    def test_sync_calls_all_steps_and_returns_a_success_notification(
            self, mock_add_projects, mock_add_sections, mock_add_tasks):
        result = self.user.action_sync_todoist_with_odoo()

        mock_add_projects.assert_called_once()
        mock_add_sections.assert_called_once()
        mock_add_tasks.assert_called_once()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')
        self.assertEqual(
            result['params']['next'],
            {'type': 'ir.actions.act_window_close'},
        )


class TestGetTodoistProjectsTasks(TransactionCase):
    """Test the Todoist API v1 helper, with requests mocked out so no real
    network call is made."""

    @patch(REQUESTS_PATCH_TARGET)
    def test_fetches_projects_from_the_v1_api(self, mock_get):
        mock_get.return_value = _response(results=[_make_project('a', 'P')])

        result = _get_todoist_data(self.env, 'tok', 'projects')

        self.assertEqual(result, [_make_project('a', 'P')])
        url = mock_get.call_args.args[0]
        self.assertEqual(url, 'https://api.todoist.com/api/v1/projects')
        self.assertEqual(mock_get.call_args.kwargs['headers'],
                         {'Authorization': 'Bearer tok'})

    @patch(REQUESTS_PATCH_TARGET)
    def test_fetches_tasks_and_follows_pages(self, mock_get):
        mock_get.side_effect = [
            _response(results=[{'id': '1'}], next_cursor='next'),
            _response(results=[{'id': '2'}]),
        ]

        result = _get_todoist_data(self.env, 'tok', 'tasks')

        self.assertEqual(result, [{'id': '1'}, {'id': '2'}])
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(mock_get.call_args.args[0],
                         'https://api.todoist.com/api/v1/tasks')
        self.assertEqual(mock_get.call_args.kwargs['params']['cursor'],
                         'next')

    @patch(REQUESTS_PATCH_TARGET)
    def test_invalid_token_raises_a_user_error(self, mock_get):
        mock_get.return_value = _response(status_code=401)

        with self.assertRaisesRegex(UserError, 'token is invalid'):
            _get_todoist_data(self.env, 'bad', 'projects')

    @patch(REQUESTS_PATCH_TARGET)
    def test_api_error_raises_a_user_error(self, mock_get):
        mock_get.return_value = _response(status_code=410,
                                          text='This endpoint is deprecated.')

        with self.assertRaisesRegex(UserError, '410'):
            _get_todoist_data(self.env, 'tok', 'projects')

    @patch(REQUESTS_PATCH_TARGET)
    def test_connection_error_raises_a_user_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError(
            'network down')

        with self.assertRaisesRegex(UserError, 'Could not connect'):
            _get_todoist_data(self.env, 'tok', 'projects')

    @patch(REQUESTS_PATCH_TARGET)
    def test_sync_button_shows_the_error_instead_of_crashing(self, mock_get):
        """The tester's case: the API refusal must reach the user as a
        message, not as a TypeError traceback"""
        self.env.user.todoist_token = 'tok'
        mock_get.return_value = _response(status_code=410)

        with self.assertRaises(UserError):
            self.env.user.action_sync_todoist_with_odoo()


class TestUserAccess(TransactionCase):
    """Test the feature as real users instead of the superuser."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project_user = new_test_user(
            cls.env, login='todoist_project_user',
            groups='base.group_user,project.group_project_user')
        cls.other_user = new_test_user(
            cls.env, login='todoist_other_user', groups='base.group_user')

    def test_user_saves_and_reads_their_own_token(self):
        user = self.project_user.with_user(self.project_user)
        user.write({'todoist_token': 'own-token'})
        self.assertEqual(user.todoist_token, 'own-token')
        self.assertEqual(
            user.web_read({'todoist_token': {}})[0]['todoist_token'],
            'own-token')

    def test_other_users_cannot_read_the_token(self):
        self.project_user.sudo().todoist_token = 'own-token'
        with self.assertRaises(AccessError):
            self.project_user.with_user(self.other_user).read(
                ['todoist_token'])

    def test_preferences_form_shows_the_token_to_project_users(self):
        arch = self.env['res.users'].with_user(self.project_user).get_view(
            self.env.ref('base.view_users_form_simple_modif').id)['arch']
        self.assertIn('todoist_token', arch)
        self.assertIn('action_sync_todoist_with_odoo', arch)

    @patch(FETCH_PATCH_TARGET)
    def test_project_user_runs_the_sync(self, mock_fetch):
        mock_fetch.side_effect = [
            [_make_project('p1', 'Synced')], [],
            [_make_task('t1', 'p1', 'Synced task')],
        ]
        self.project_user.sudo().todoist_token = 'own-token'
        self.project_user.with_user(
            self.project_user).action_sync_todoist_with_odoo()
        task = self.env['project.task'].search([('todo_task', '=', 't1')])
        self.assertEqual(task.project_id.name, 'Synced')

    def test_sync_is_refused_without_project_rights(self):
        self.other_user.sudo().todoist_token = 'own-token'
        with self.assertRaises(AccessError):
            self.other_user.with_user(
                self.other_user).action_sync_todoist_with_odoo()

    def test_sync_with_the_token_of_another_user_is_refused(self):
        self.other_user.sudo().todoist_token = 'other-token'
        with self.assertRaises(AccessError):
            self.other_user.with_user(
                self.project_user).action_sync_todoist_with_odoo()


class TestCopiesAndArchives(TransactionCase):
    """Test the link with Todoist on copied and archived records."""

    @patch(FETCH_PATCH_TARGET)
    def test_copies_are_not_linked_and_archives_are_reused(self, mock_fetch):
        project = self.env['project.project'].create({
            'name': 'Archived', 'todo_project': 'p9', 'active': False})
        self.assertFalse(project.copy().todo_project)
        self.env.user.todoist_token = 'own-token'
        mock_fetch.return_value = [_make_project('p9', 'Archived')]
        self.env.user._add_all_projects()
        self.assertEqual(self.env['project.project'].with_context(
            active_test=False).search_count(
                [('todo_project', '=', 'p9')]), 1)

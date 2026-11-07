# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger

from odoo.addons.project_task_unique_code.hooks import assign_project_codes


@tagged('post_install', '-at_install')
class TestTaskUniqueCode(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Project = self.env['project.project']
        self.Task = self.env['project.task']
        # Created per test: sequence numbers come from PostgreSQL sequences,
        # which a test rollback does not reset.
        self.project = self.Project.create({'name': 'Website', 'project_short_code': 'WEB'})

    def test_task_gets_code_from_project_sequence(self):
        first = self.Task.create({'name': 'Home page', 'project_id': self.project.id})
        second = self.Task.create({'name': 'Contact page', 'project_id': self.project.id})
        self.assertEqual(self.project.sequence_id.prefix, 'WEB-')
        self.assertEqual(first.unique_code, 'WEB-001')
        self.assertEqual(second.unique_code, 'WEB-002')

    def test_task_created_inside_project(self):
        """The project kanban passes the project in the context, not in the values."""
        task = self.Task.with_context(default_project_id=self.project.id).create({'name': 'Blog'})
        self.assertEqual(task.unique_code, 'WEB-001')

    def test_task_moved_into_project_gets_code(self):
        task = self.Task.create({'name': 'Private'})
        self.assertFalse(task.unique_code)
        task.project_id = self.project
        self.assertEqual(task.unique_code, 'WEB-001')
        other = self.Project.create({'name': 'Other', 'project_short_code': 'OTH'})
        task.project_id = other
        self.assertEqual(task.unique_code, 'WEB-001', "an existing code is kept")

    def test_copied_task_gets_new_code(self):
        task = self.Task.create({'name': 'Logo', 'project_id': self.project.id})
        copy = task.copy()
        self.assertEqual(copy.unique_code, 'WEB-002')

    def test_project_created_without_code(self):
        """Projects created by code or other modules get a generated code."""
        project = self.Project.create({'name': 'Mobile app!'})
        self.assertEqual(project.project_short_code, 'MOBI')
        self.assertEqual(project.sequence_id.prefix, 'MOBI-')
        twin = self.Project.create({'name': 'Mobile backend'})
        self.assertEqual(twin.project_short_code, 'MOBI2')
        self.assertEqual(self.Project.create({'name': '***'}).project_short_code, 'PRJ')

    def test_project_copy(self):
        copy = self.project.copy()
        self.assertTrue(copy.project_short_code)
        self.assertNotEqual(copy.project_short_code, self.project.project_short_code)
        self.assertNotEqual(copy.sequence_id, self.project.sequence_id)

    def test_changing_code_updates_prefix(self):
        self.project.project_short_code = 'SITE'
        task = self.Task.create({'name': 'Footer', 'project_id': self.project.id})
        self.assertEqual(task.unique_code, 'SITE-001')

    def test_short_code_unique_per_company(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.Project.create({'name': 'Again', 'project_short_code': 'WEB'})
            self.env.flush_all()

    def test_post_install_hook_fills_existing_projects(self):
        self.env.cr.execute(
            "UPDATE project_project SET project_short_code = NULL, sequence_id = NULL WHERE id = %s",
            (self.project.id,))
        self.env.invalidate_all()
        assign_project_codes(self.env)
        self.assertEqual(self.project.project_short_code, 'WEBS')
        self.assertTrue(self.project.sequence_id)

    def test_project_user_creates_task(self):
        user = new_test_user(self.env, login='ptuc_user', groups='base.group_user,project.group_project_user')
        task = self.Task.with_user(user).create({'name': 'By user', 'project_id': self.project.id})
        self.assertEqual(task.unique_code, 'WEB-001')

    def test_portal_collaborator_creates_task(self):
        """Project sharing: a portal user can create tasks although sequences are hidden from portal."""
        portal = new_test_user(self.env, login='ptuc_portal', groups='base.group_portal')
        self.project.write({
            'privacy_visibility': 'portal',
            'collaborator_ids': [(0, 0, {'partner_id': portal.partner_id.id, 'access_mode': 'edit'})],
        })
        task = self.Task.with_user(portal).with_context(default_project_id=self.project.id).create(
            {'name': 'From portal'})
        self.assertEqual(task.sudo().unique_code, 'WEB-001')

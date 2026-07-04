# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestAdvancedProjectManagementSystem(TransactionCase):

    def setUp(self):
        super().setUp()
        self.category = self.env['project.category'].create({
            'name': 'Development',
            'is_active': True,
        })
        self.project = self.env['project.project'].create({
            'name': 'Test Project Alpha',
            'project_category_id': self.category.id,
        })
        self.checklist = self.env['project.checklist'].create({
            'name': 'Setup Environment',
            'description': 'Configure the development environment',
            'company_id': self.env.company.id,
        })
        self.task = self.env['project.task'].create({
            'name': 'Initial Task',
            'project_id': self.project.id,
            'task_type': 'task',
        })

    def test_01_project_category_creation(self):
        self.assertEqual(self.category.name, 'Development')
        self.assertTrue(self.category.is_active)

    def test_02_project_creation_with_category(self):
        self.assertEqual(self.project.name, 'Test Project Alpha')
        self.assertEqual(self.project.project_category_id.id, self.category.id)

    def test_03_project_checklist_creation(self):
        self.assertEqual(self.checklist.name, 'Setup Environment')
        self.assertEqual(self.checklist.description,
                         'Configure the development environment')
        self.assertEqual(self.checklist.company_id.id, self.env.company.id)

    def test_04_project_checklist_info_creation(self):
        checklist_info = self.env['project.checklist.info'].create({
            'checklist_id': self.checklist.id,
            'project_id': self.project.id,
            'state': 'new',
        })
        self.assertEqual(checklist_info.project_id.id, self.project.id)
        self.assertEqual(checklist_info.state, 'new')

    def test_05_checklist_info_complete_action(self):
        checklist_info = self.env['project.checklist.info'].create({
            'checklist_id': self.checklist.id,
            'project_id': self.project.id,
            'state': 'new',
        })
        checklist_info.action_set_checklist_complete()
        self.assertEqual(checklist_info.state, 'done')

    def test_06_checklist_info_cancel_action(self):
        checklist_info = self.env['project.checklist.info'].create({
            'checklist_id': self.checklist.id,
            'project_id': self.project.id,
            'state': 'new',
        })
        checklist_info.action_set_checklist_close()
        self.assertEqual(checklist_info.state, 'cancel')

    def test_07_checklist_progress_updates_on_complete(self):
        info1 = self.env['project.checklist.info'].create({
            'checklist_id': self.checklist.id,
            'project_id': self.project.id,
            'state': 'new',
        })
        info2 = self.env['project.checklist.info'].create({
            'checklist_id': self.checklist.id,
            'project_id': self.project.id,
            'state': 'new',
        })
        info1.action_set_checklist_complete()
        self.assertGreater(self.project.checklist_progress, 0)

    def test_08_task_creation_with_type(self):
        self.assertEqual(self.task.name, 'Initial Task')
        self.assertEqual(self.task.task_type, 'task')
        self.assertEqual(self.task.project_id.id, self.project.id)

    def test_09_task_type_bug(self):
        bug_task = self.env['project.task'].create({
            'name': 'Bug Task',
            'project_id': self.project.id,
            'task_type': 'bug',
        })
        self.assertEqual(bug_task.task_type, 'bug')

    def test_10_task_type_subtask(self):
        subtask = self.env['project.task'].create({
            'name': 'Sub Task',
            'project_id': self.project.id,
            'task_type': 'subtask',
        })
        self.assertEqual(subtask.task_type, 'subtask')

    def test_11_task_checklist_progress_constraint_valid(self):
        self.task.checklist_progress = 0.5
        self.task._check_checklist_progress()
        self.assertEqual(self.task.checklist_progress, 0.5)

    def test_12_task_checklist_progress_constraint_invalid(self):
        with self.assertRaises(ValidationError):
            self.task.checklist_progress = 1.5
            self.task._check_checklist_progress()

    def test_13_task_document_count(self):
        self.env['ir.attachment'].create({
            'name': 'test_document.pdf',
            'res_model': 'project.task',
            'res_id': self.task.id,
            'datas': b'',
        })
        self.task._compute_document_count()
        self.assertEqual(self.task.document_count, 1)

    def test_14_project_document_count(self):
        self.env['ir.attachment'].create({
            'name': 'project_document.pdf',
            'res_model': 'project.project',
            'res_id': self.project.id,
            'datas': b'',
        })
        self.project._compute_document_count()
        self.assertEqual(self.project.document_count, 1)

    def test_15_project_issue_creation(self):
        issue = self.env['project.issue'].create({
            'project_id': self.project.id,
            'task_id': self.task.id,
            'summary': 'Test issue summary',
            'priority': '1',
            'state': 'new',
        })
        self.assertNotEqual(issue.name, 'new')
        self.assertEqual(issue.state, 'new')
        self.assertEqual(issue.project_id.id, self.project.id)

    def test_16_project_issue_state_transitions(self):
        issue = self.env['project.issue'].create({
            'project_id': self.project.id,
            'summary': 'State transition test',
            'state': 'new',
        })
        issue.state = 'progress'
        self.assertEqual(issue.state, 'progress')
        issue.state = 'done'
        self.assertEqual(issue.state, 'done')

    def test_17_project_issue_count(self):
        self.env['project.issue'].create({
            'project_id': self.project.id,
            'summary': 'Issue one',
        })
        self.env['project.issue'].create({
            'project_id': self.project.id,
            'summary': 'Issue two',
        })
        self.project._compute_issue_count()
        self.assertEqual(self.project.issue_count, 2)

    def test_18_project_url_shortcut_with_link(self):
        self.project.url_link = 'https://www.example.com'
        self.project.url_name = 'Example Site'
        self.project._compute_url_shortcut()
        self.assertTrue(self.project.is_active)
        self.assertEqual(self.project.url_shortcut, 'https://www.example.com')

    def test_19_project_url_shortcut_without_link(self):
        self.project.url_link = False
        self.project._compute_url_shortcut()
        self.assertFalse(self.project.is_active)
        self.assertEqual(self.project.url_shortcut, 'Add Link')

    def test_20_task_checklist_info_creation(self):
        task_checklist = self.env['project.task.checklist'].create({
            'name': 'Write unit tests',
            'description': 'Cover all model methods',
            'company_id': self.env.company.id,
        })
        task_checklist_info = self.env['project.task.checklist.info'].create({
            'checklist_id': task_checklist.id,
            'task_id': self.task.id,
            'state': 'new',
        })
        self.assertEqual(task_checklist_info.task_id.id, self.task.id)
        self.assertEqual(task_checklist_info.state, 'new')

    def test_21_task_checklist_info_cancel(self):
        task_checklist = self.env['project.task.checklist'].create({
            'name': 'Cancel Test Item',
            'description': 'Item to be cancelled',
            'company_id': self.env.company.id,
        })
        task_checklist_info = self.env['project.task.checklist.info'].create({
            'checklist_id': task_checklist.id,
            'task_id': self.task.id,
            'state': 'new',
        })
        task_checklist_info.action_set_checklist_close()
        self.assertEqual(task_checklist_info.state, 'cancel')

    def test_22_project_task_type_with_multiple_users(self):
        user1 = self.env['res.users'].create({
            'name': 'Test User One',
            'login': 'testuser1_apms@test.com',
        })
        user2 = self.env['res.users'].create({
            'name': 'Test User Two',
            'login': 'testuser2_apms@test.com',
        })
        stage = self.env['project.task.type'].create({
            'name': 'In Review',
            'user_ids': [(6, 0, [user1.id, user2.id])],
        })
        self.assertIn(user1.id, stage.user_ids.ids)
        self.assertIn(user2.id, stage.user_ids.ids)

    def test_23_multiple_categories_for_projects(self):
        cat2 = self.env['project.category'].create({
            'name': 'Marketing',
            'is_active': True,
        })
        project2 = self.env['project.project'].create({
            'name': 'Marketing Campaign',
            'project_category_id': cat2.id,
        })
        self.assertEqual(project2.project_category_id.name, 'Marketing')
        self.assertNotEqual(project2.project_category_id.id,
                            self.project.project_category_id.id)

    def test_24_issue_sequence_auto_generated(self):
        issue1 = self.env['project.issue'].create({
            'project_id': self.project.id,
            'summary': 'First issue',
        })
        issue2 = self.env['project.issue'].create({
            'project_id': self.project.id,
            'summary': 'Second issue',
        })
        self.assertNotEqual(issue1.name, issue2.name)
        self.assertNotEqual(issue1.name, 'new')

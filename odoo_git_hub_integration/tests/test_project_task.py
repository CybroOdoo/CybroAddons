# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestProjectTask(TransactionCase):
    """Test cases for the ProjectTask GitHub extension (project.task)."""

    def setUp(self):
        super().setUp()
        self.config = self.env['github.config'].create({
            'name': 'Test Config',
            'access_token': 'test_token_abc',
            'username': 'testuser',
        })
        self.project = self.env['project.project'].create({'name': 'Task Test Project'})
        self.repo = self.env['github.repository'].create({
            'name': 'task-test-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/task-test-repo',
        })
        self.project.write({'github_repository_id': self.repo.id})
        self.task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.project.id,
        })
        self.issue = self.env['github.issue'].create({
            'repository_id': self.repo.id,
            'github_id': 'gh_issue_100',
            'number': 100,
            'title': 'Test GitHub Issue',
            'state': 'open',
            'github_url': 'https://github.com/testuser/task-test-repo/issues/100',
        })
        self.task.write({'github_issue_id': self.issue.id})

    def test_task_creation(self):
        """Test that project.task record includes GitHub fields."""
        self.assertTrue(self.task.id)
        self.assertEqual(self.task.github_issue_id.id, self.issue.id)

    def test_compute_commits_count(self):
        """Test commits_count is 0 when no commits are linked."""
        self.assertEqual(self.task.commits_count, 0)

    def test_action_view_github_issue(self):
        """Test action_view_github_issue opens the linked issue URL."""
        result = self.task.action_view_github_issue()
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertEqual(result['url'], self.issue.github_url)

    def test_action_view_commits(self):
        """Test action_view_commits returns a list view of commits."""
        result = self.task.action_view_commits()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'github.commit')
        self.assertIn('list', result['view_mode'])

    def test_action_export_to_github_already_linked(self):
        """Test action_export_to_github raises UserError if task already linked to issue."""
        with self.assertRaises(UserError):
            self.task.action_export_to_github()

    def test_action_export_to_github_no_repo(self):
        """Test action_export_to_github raises UserError if task has no repository."""
        project_no_repo = self.env['project.project'].create({'name': 'No Repo Project'})
        task_no_repo = self.env['project.task'].create({
            'name': 'Task Without Repo',
            'project_id': project_no_repo.id,
        })
        with self.assertRaises(UserError):
            task_no_repo.action_export_to_github()

    def test_action_open_pr_wizard_no_repo(self):
        """Test action_open_pr_wizard raises UserError when task has no repository."""
        project_no_repo = self.env['project.project'].create({'name': 'No Repo Project 2'})
        task_no_repo = self.env['project.task'].create({
            'name': 'No Repo Task',
            'project_id': project_no_repo.id,
        })
        with self.assertRaises(UserError):
            task_no_repo.action_open_pr_wizard()

    def test_action_open_pr_wizard_with_repo(self):
        """Test action_open_pr_wizard returns the wizard form action when repo is set."""
        task = self.env['project.task'].create({
            'name': 'Task With Repo',
            'project_id': self.project.id,
            'github_branch_name': 'feature-x',
        })
        result = task.action_open_pr_wizard()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'github.pull.request.wizard')
        self.assertEqual(result['context']['default_head_branch'], 'feature-x')

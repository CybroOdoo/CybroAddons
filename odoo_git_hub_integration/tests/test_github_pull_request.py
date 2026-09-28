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


class TestGitHubPullRequest(TransactionCase):
    """Test cases for the GitHubPullRequest model (github.pull.request)."""

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].create({'name': 'PR Test Project'})
        self.repo = self.env['github.repository'].create({
            'name': 'pr-test-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/pr-test-repo',
            'project_ids': [(4, self.project.id)],
        })
        self.branch_main = self.env['github.branch'].create({
            'name': 'main',
            'repository_id': self.repo.id,
            'github_url': 'https://github.com/testuser/pr-test-repo/tree/main',
        })
        self.branch_feature = self.env['github.branch'].create({
            'name': 'feature-branch',
            'repository_id': self.repo.id,
            'github_url': 'https://github.com/testuser/pr-test-repo/tree/feature-branch',
        })
        self.pr = self.env['github.pull.request'].create({
            'repository_id': self.repo.id,
            'github_id': 'gh_pr_001',
            'number': 1,
            'title': 'Test Pull Request',
            'body': 'This is a test PR description.',
            'state': 'open',
            'github_url': 'https://github.com/testuser/pr-test-repo/pulls/1',
            'head_branch': 'feature-branch',
            'base_branch': 'main',
        })

    def test_pr_creation(self):
        """Test that a pull request record is created with correct data."""
        self.assertTrue(self.pr.id)
        self.assertEqual(self.pr.title, 'Test Pull Request')
        self.assertEqual(self.pr.state, 'open')

    def test_link_branches_on_create(self):
        """Test that branches are linked after PR creation."""
        self.assertEqual(self.pr.head_branch_id.id, self.branch_feature.id)
        self.assertEqual(self.pr.base_branch_id.id, self.branch_main.id)

    def test_action_create_task(self):
        """Test action_create_task creates an Odoo task from the PR."""
        self.pr.action_create_task()
        task = self.env['project.task'].search([
            ('github_pr_id', '=', self.pr.id),
            ('project_id', '=', self.project.id),
        ], limit=1)
        self.assertTrue(task, "A task should be created from the pull request.")
        self.assertIn('PR #1', task.name)

    def test_action_create_task_already_exists(self):
        """Test action_create_task returns existing task if already linked."""
        self.pr.action_create_task()
        # Call again — should not create a duplicate
        self.pr.action_create_task()
        task_count = self.env['project.task'].search_count([
            ('github_pr_id', '=', self.pr.id),
        ])
        self.assertEqual(task_count, 1, "Only one task should exist for the PR.")

    def test_action_create_task_no_project(self):
        """Test action_create_task raises UserError if repo has no project."""
        repo_no_proj = self.env['github.repository'].create({
            'name': 'no-proj-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/no-proj-repo',
        })
        pr_no_proj = self.env['github.pull.request'].create({
            'repository_id': repo_no_proj.id,
            'github_id': 'gh_pr_002',
            'number': 2,
            'title': 'PR Without Project',
            'state': 'open',
        })
        with self.assertRaises(UserError):
            pr_no_proj.action_create_task()

    def test_write_updates_branch_links(self):
        """Test that writing head_branch or base_branch re-links branch records."""
        self.pr.write({'head_branch': 'main', 'base_branch': 'feature-branch'})
        self.assertEqual(self.pr.head_branch_id.id, self.branch_main.id)
        self.assertEqual(self.pr.base_branch_id.id, self.branch_feature.id)

    def test_unique_github_id_per_repo(self):
        """Test that duplicate github_id per repo raises an error."""
        constraints = [c[0] for c in self.env['github.pull.request']._sql_constraints]
        self.assertIn('github_id_repo_unique', constraints)

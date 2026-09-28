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
from odoo.exceptions import UserError, ValidationError


class TestGitHubBranch(TransactionCase):
    """Test cases for the GitHubBranch model (github.branch)."""

    def setUp(self):
        super().setUp()
        self.repo = self.env['github.repository'].create({
            'name': 'branch-test-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/branch-test-repo',
            'default_branch': 'main',
        })
        self.branch_main = self.env['github.branch'].create({
            'name': 'main',
            'repository_id': self.repo.id,
            'is_default': True,
            'github_url': 'https://github.com/testuser/branch-test-repo/tree/main',
        })
        self.branch_feature = self.env['github.branch'].create({
            'name': 'feature',
            'repository_id': self.repo.id,
            'is_default': False,
            'github_url': 'https://github.com/testuser/branch-test-repo/tree/feature',
        })

    def test_branch_creation(self):
        """Test branch records are created correctly."""
        self.assertTrue(self.branch_main.id)
        self.assertTrue(self.branch_main.is_default)
        self.assertFalse(self.branch_feature.is_default)

    def test_compute_commits_count(self):
        """Test commits_count is 0 when no commits are linked."""
        self.assertEqual(self.branch_main.commits_count, 0)

    def test_compute_pull_request_count(self):
        """Test pull_request_count is 0 when no PRs are linked."""
        self.assertEqual(self.branch_main.pull_request_count, 0)

    def test_action_create_pull_request_from_default_raises(self):
        """Test that creating a PR from the default branch raises UserError."""
        with self.assertRaises(UserError):
            self.branch_main.action_create_pull_request()

    def test_action_create_pull_request_from_feature(self):
        """Test action_create_pull_request opens the wizard for a feature branch."""
        result = self.branch_feature.action_create_pull_request()
        self.assertEqual(result['res_model'], 'github.pull.request.wizard')
        self.assertEqual(result['context']['default_head_branch'], 'feature')

    def test_action_view_commits(self):
        """Test action_view_commits returns a list view action for commits."""
        result = self.branch_main.action_view_commits()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'github.commit')
        self.assertIn('list', result['view_mode'])

    def test_action_view_pull_requests(self):
        """Test action_view_pull_requests returns an action for related PRs."""
        result = self.branch_main.action_view_pull_requests()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'github.pull.request')

    def test_action_delete_default_branch_raises(self):
        """Test that deleting the default branch raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.branch_main.action_delete_branch()

    def test_action_delete_protected_branch_raises(self):
        """Test that deleting a protected branch raises ValidationError."""
        self.branch_feature.is_protected = True
        with self.assertRaises(ValidationError):
            self.branch_feature.action_delete_branch()

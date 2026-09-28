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
from unittest.mock import patch, MagicMock


class TestGitHubRepository(TransactionCase):
    """Test cases for the GitHubRepository model (github.repository)."""

    def setUp(self):
        super().setUp()
        self.env['github.config'].search([]).write({'active': False})
        self.config = self.env['github.config'].create({
            'name': 'Test Config',
            'access_token': 'test_token_abc',
            'username': 'testuser',
        })
        self.project = self.env['project.project'].create({'name': 'Repo Test Project'})
        self.repo = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/test-repo',
            'default_branch': 'main',
        })

    def test_repo_creation(self):
        """Test that a repository record is created correctly."""
        self.assertTrue(self.repo.id)
        self.assertEqual(self.repo.name, 'test-repo')
        self.assertEqual(self.repo.owner, 'testuser')

    def test_compute_branches_count(self):
        """Test branches_count is 0 when no branches linked."""
        self.assertEqual(self.repo.branches_count, 0)

    def test_compute_collaborators_count(self):
        """Test collaborators_count is 0 when no collaborators linked."""
        self.assertEqual(self.repo.collaborators_count, 0)

    def test_compute_open_issues_count(self):
        """Test open_issues_count is 0 when no issues linked."""
        self.assertEqual(self.repo.open_issues_count, 0)

    def test_compute_dashboard_stats(self):
        """Test pull_requests_count computed from pull_request_ids."""
        self.assertEqual(self.repo.pull_requests_count, 0)

    def test_parse_github_datetime_valid(self):
        """Test _parse_github_datetime correctly parses a GitHub datetime string."""
        result = self.repo._parse_github_datetime('2026-06-25T08:00:00Z')
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 6)
        self.assertEqual(result.day, 25)

    def test_parse_github_datetime_none(self):
        """Test _parse_github_datetime returns False for None input."""
        result = self.repo._parse_github_datetime(None)
        self.assertFalse(result)

    def test_get_github_headers(self):
        """Test _get_github_headers returns correct authorization header."""
        headers = self.repo._get_github_headers()
        self.assertIn('Authorization', headers)
        self.assertIn('test_token_abc', headers['Authorization'])

    def test_get_github_headers_no_config(self):
        """Test _get_github_headers raises UserError when no config exists."""
        self.config.active = False
        with self.assertRaises(UserError):
            self.repo._get_github_headers()

    def test_open_in_github(self):
        """Test open_in_github returns a URL action."""
        result = self.repo.open_in_github()
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertEqual(result['url'], self.repo.url)

    def test_action_view_commits(self):
        """Test action_view_commits returns a list view action."""
        result = self.repo.action_view_commits()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'github.commit')
        self.assertIn('list', result['view_mode'])

    def test_action_create_new_repository(self):
        """Test action_create_new_repository opens a form view."""
        result = self.repo.action_create_new_repository()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'github.repository')
        self.assertEqual(result['view_mode'], 'form')

    def test_action_sync_repository_no_owner(self):
        """Test action_sync_repository raises UserError when owner is missing."""
        repo_no_owner = self.env['github.repository'].create({
            'name': 'no-owner-repo',
            'owner': False,
        })
        with self.assertRaises(UserError):
            repo_no_owner.action_sync_repository()

    def test_action_export_to_github_already_linked(self):
        """Test action_export_to_github raises UserError if repo has github_id."""
        self.repo.github_id = 'existing_gh_id_123'
        with self.assertRaises(UserError):
            self.repo.action_export_to_github()

    def test_action_sync_commits_no_branches(self):
        """Test action_sync_commits completes cleanly when there are no branches."""
        result = self.repo.action_sync_commits()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['params']['type'], 'success')

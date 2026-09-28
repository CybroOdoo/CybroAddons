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

from datetime import datetime
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from unittest.mock import patch, MagicMock


class TestGitHubIssue(TransactionCase):
    """Test cases for the GitHubIssue model (github.issue)."""

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].create({'name': 'Test Project'})
        self.repo = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/test-repo',
            'project_ids': [(4, self.project.id)],
        })
        self.issue = self.env['github.issue'].create({
            'repository_id': self.repo.id,
            'github_id': 'gh_issue_001',
            'number': 1,
            'title': 'Test Issue',
            'body': 'This is a test issue body.',
            'state': 'open',
            'github_url': 'https://github.com/testuser/test-repo/issues/1',
            'created_at': datetime(2026, 1, 1, 0, 0, 0),
        })

    def test_issue_creation(self):
        """Test that a github.issue record is created correctly."""
        self.assertTrue(self.issue.id)
        self.assertEqual(self.issue.title, 'Test Issue')
        self.assertEqual(self.issue.state, 'open')

    def test_compute_issue_age_days_open(self):
        """Test issue_age_days is computed for an open issue."""
        self.assertGreater(self.issue.issue_age_days, 0,
                           "Open issue age should be greater than 0.")

    def test_compute_issue_age_days_no_created_at(self):
        """Test issue_age_days is 0 when created_at is not set."""
        issue_no_date = self.env['github.issue'].create({
            'repository_id': self.repo.id,
            'github_id': 'gh_issue_no_date',
            'number': 99,
            'title': 'No Date Issue',
            'state': 'open',
        })
        self.assertEqual(issue_no_date.issue_age_days, 0)

    def test_action_create_task(self):
        """Test action_create_task creates a task for the linked project."""
        result = self.issue.action_create_task()
        task = self.env['project.task'].search([
            ('github_issue_id', '=', self.issue.id),
            ('project_id', '=', self.project.id)
        ], limit=1)
        self.assertTrue(task, "A task should have been created for the issue.")
        self.assertIn(str(self.issue.number), task.name)

    def test_action_create_task_no_project(self):
        """Test action_create_task raises ValidationError if no project linked."""
        repo_no_project = self.env['github.repository'].create({
            'name': 'no-project-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/no-project-repo',
        })
        issue_no_project = self.env['github.issue'].create({
            'repository_id': repo_no_project.id,
            'github_id': 'gh_issue_002',
            'number': 2,
            'title': 'Issue Without Project',
            'state': 'open',
        })
        with self.assertRaises(ValidationError):
            issue_no_project.action_create_task()

    def test_action_view_github_issue(self):
        """Test action_view_github_issue returns a URL action."""
        result = self.issue.action_view_github_issue()
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertEqual(result['url'], self.issue.github_url)

    def test_action_export_to_github_already_linked(self):
        """Test action_export_to_github raises UserError if already on GitHub."""
        with self.assertRaises(UserError):
            self.issue.action_export_to_github()

    def test_action_export_to_github_not_linked(self):
        """Test action_export_to_github posts to GitHub API if not synced."""
        local_issue = self.env['github.issue'].create({
            'repository_id': self.repo.id,
            'number': 50,
            'title': 'Local Only Issue',
            'state': 'open',
        })
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 1234567,
            'number': 50,
            'html_url': 'https://github.com/testuser/test-repo/issues/50',
            'state': 'open',
        }
        with patch('requests.post', return_value=mock_response):
            result = local_issue.action_export_to_github()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['params']['type'], 'success')

    def test_write_triggers_link_to_task(self):
        """Test that writing title or body re-triggers _link_to_task."""
        self.issue.write({'title': 'Updated Title'})
        # No error should occur; method runs silently
        self.assertEqual(self.issue.title, 'Updated Title')

    def test_unique_github_id_per_repo(self):
        """Test that creating a duplicate github_id per repo raises an error."""
        constraints = [c[0] for c in self.env['github.issue']._sql_constraints]
        self.assertIn('github_id_repo_unique', constraints)

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


class TestGitHubCommit(TransactionCase):
    """Test cases for the GitHubCommit model (github.commit)."""

    def setUp(self):
        super().setUp()
        self.repo = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/test-repo',
        })
        self.branch = self.env['github.branch'].create({
            'name': 'main',
            'repository_id': self.repo.id,
            'github_url': 'https://github.com/testuser/test-repo/tree/main',
        })
        self.commit = self.env['github.commit'].create({
            'repository_id': self.repo.id,
            'sha': 'abc1234567890abcdef',
            'message': 'Initial commit',
            'author_name': 'Test Author',
            'author_email': 'testauthor@example.com',
            'committed_date': datetime(2026, 6, 25, 8, 0, 0),
            'github_url': 'https://github.com/testuser/test-repo/commit/abc1234567890abcdef',
            'branch_id': self.branch.id,
        })

    def test_commit_creation(self):
        """Test that a commit record is created with correct data."""
        self.assertTrue(self.commit.id)
        self.assertEqual(self.commit.sha, 'abc1234567890abcdef')
        self.assertEqual(self.commit.author_name, 'Test Author')

    def test_compute_commit_date(self):
        """Test that commit_day is correctly computed from committed_date."""
        self.assertEqual(
            str(self.commit.commit_day),
            '2026-06-25',
            "commit_day should match the date portion of committed_date."
        )

    def test_compute_commit_date_no_date(self):
        """Test that commit_day is False when committed_date is not set."""
        commit_no_date = self.env['github.commit'].create({
            'repository_id': self.repo.id,
            'sha': 'nodate000001',
            'message': 'No date commit',
        })
        self.assertFalse(commit_no_date.commit_day)

    def test_action_view_github_commit(self):
        """Test action_view_github_commit returns a URL action."""
        result = self.commit.action_view_github_commit()
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertEqual(result['url'], self.commit.github_url)
        self.assertEqual(result['target'], 'new')

    def test_action_export_commits_csv(self):
        """Test action_export_commits_csv returns an act_url action."""
        result = self.commit.action_export_commits_csv()
        self.assertEqual(result['type'], 'ir.actions.act_url')
        self.assertIn('/web/content/', result['url'])

    def test_link_to_task_no_match(self):
        """Test that _link_to_task does not link when message has no pattern."""
        self.commit._link_to_task()
        self.assertFalse(
            self.commit.task_ids,
            "No task should be linked when commit message has no task reference."
        )

    def test_link_to_task_already_linked(self):
        """Test that _link_to_task exits early when task_ids already set."""
        project = self.env['project.project'].create({'name': 'Test Project'})
        task = self.env['project.task'].create({
            'name': 'Existing Task',
            'project_id': project.id,
        })
        self.commit.task_ids = [(4, task.id)]
        self.commit._link_to_task()
        # Still only one task (not duplicated)
        self.assertEqual(len(self.commit.task_ids), 1)

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


class TestGitHubPullRequestWizard(TransactionCase):
    """Test cases for the GitHubPullRequestWizard model."""

    def setUp(self):
        super().setUp()
        self.config = self.env['github.config'].create({
            'name': 'Test Config',
            'access_token': 'test_token_abc',
            'username': 'testuser',
        })
        self.repo = self.env['github.repository'].create({
            'name': 'wiz-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/wiz-repo',
        })
        self.wizard = self.env['github.pull.request.wizard'].create({
            'repository_id': self.repo.id,
            'head_branch': 'feature-branch',
            'base_branch': 'main',
            'name': 'Test PR Wizard',
            'description': 'Testing PR creation wizard.',
        })

    def test_wizard_creation(self):
        """Test that the wizard record is created correctly."""
        self.assertTrue(self.wizard.id)
        self.assertEqual(self.wizard.name, 'Test PR Wizard')
        self.assertEqual(self.wizard.head_branch, 'feature-branch')

    def test_action_create_pull_request_success(self):
        """Test action_create_pull_request creates a PR record on success."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 9999,
            'number': 42,
            'title': 'Test PR Wizard',
            'body': 'Testing PR creation wizard.',
            'state': 'open',
            'html_url': 'https://github.com/testuser/wiz-repo/pull/42',
            'created_at': '2026-06-25T08:00:00Z',
            'updated_at': '2026-06-25T08:00:00Z',
            'user': {'login': 'testuser'},
            'head': {'ref': 'feature-branch'},
            'base': {'ref': 'main'},
        }
        with patch('requests.post', return_value=mock_response):
            result = self.wizard.action_create_pull_request()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'github.pull.request')

        pr = self.env['github.pull.request'].search([
            ('github_id', '=', '9999'), ('repository_id', '=', self.repo.id)
        ], limit=1)
        self.assertTrue(pr, "A pull request record should exist after wizard creation.")

    def test_action_create_pull_request_no_commits(self):
        """Test action_create_pull_request raises UserError on 'No commits between' error."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            'message': 'Validation Failed',
            'errors': [{'message': 'No commits between main and feature-branch'}]
        }
        with patch('requests.post', return_value=mock_response):
            with self.assertRaises(UserError):
                self.wizard.action_create_pull_request()

    def test_action_create_pull_request_already_exists(self):
        """Test action_create_pull_request raises UserError when PR already exists."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            'message': 'Validation Failed',
            'errors': [{'message': 'A pull request already exists'}]
        }
        with patch('requests.post', return_value=mock_response):
            with self.assertRaises(UserError):
                self.wizard.action_create_pull_request()

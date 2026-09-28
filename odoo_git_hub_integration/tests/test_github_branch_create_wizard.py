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
from unittest.mock import patch, MagicMock


class TestGitHubBranchCreateWizard(TransactionCase):
    """Test cases for the GitHubBranchCreateWizard model."""

    def setUp(self):
        super().setUp()
        self.config = self.env['github.config'].create({
            'name': 'Test Config',
            'access_token': 'test_token_xyz',
            'username': 'testuser',
        })
        self.repo = self.env['github.repository'].create({
            'name': 'branch-wiz-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/branch-wiz-repo',
            'default_branch': 'main',
        })
        self.wizard = self.env['github.branch.create.wizard'].create({
            'repository_id': self.repo.id,
            'branch_name': 'new-feature',
            'base_branch_name': 'main',
        })

    def test_wizard_creation(self):
        """Test wizard record is created correctly."""
        self.assertTrue(self.wizard.id)
        self.assertEqual(self.wizard.branch_name, 'new-feature')
        self.assertEqual(self.wizard.base_branch_name, 'main')

    def test_default_get_sets_base_branch(self):
        """Test default_get sets base_branch_name from repository default_branch."""
        wizard_with_context = self.env['github.branch.create.wizard'].with_context(
            default_repository_id=self.repo.id
        )
        defaults = wizard_with_context.default_get(['base_branch_name', 'repository_id'])
        self.assertEqual(defaults.get('base_branch_name'), 'main')

    def test_action_confirm_create_success(self):
        """Test action_confirm_create calls repository branch creation and closes wizard."""
        with patch.object(
            type(self.repo), 'create_new_github_branch', return_value={'type': 'ir.actions.act_window'}
        ):
            result = self.wizard.action_confirm_create()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')

    def test_action_confirm_create_calls_repo_method(self):
        """Test that action_confirm_create delegates to create_new_github_branch."""
        call_tracker = []

        def mock_create_branch(name, base):
            call_tracker.append((name, base))
            return {}

        with patch.object(type(self.repo), 'create_new_github_branch', side_effect=mock_create_branch):
            self.wizard.action_confirm_create()

        self.assertEqual(len(call_tracker), 1)
        self.assertEqual(call_tracker[0][0], 'new-feature')
        self.assertEqual(call_tracker[0][1], 'main')

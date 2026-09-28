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


class TestProjectProject(TransactionCase):
    """Test cases for the ProjectProject extension in github integration."""

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].create({'name': 'GitHub Project'})
        self.repo = self.env['github.repository'].create({
            'name': 'proj-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/proj-repo',
            'project_ids': [(4, self.project.id)],
        })
        self.project.write({'github_repository_id': self.repo.id})

    def test_compute_repositories_count(self):
        """Test repositories_count is computed correctly."""
        count = self.env['github.repository'].search_count(
            [('project_ids', 'in', self.project.ids)])
        self.assertEqual(self.project.repositories_count, count)

    def test_compute_open_issues_count(self):
        """Test open_issues_count is 0 for a project with no issues."""
        self.assertEqual(self.project.open_issues_count, 0)

    def test_compute_open_prs_count(self):
        """Test open_prs_count is 0 for a project with no PRs."""
        self.assertEqual(self.project.open_prs_count, 0)

    def test_compute_collaborators_count(self):
        """Test collaborators_count is 0 initially."""
        self.assertEqual(self.project.collaborators_count, 0)

    def test_action_view_details(self):
        """Test action_view_details returns a form view of the primary repository."""
        result = self.project.action_view_details()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_id'], self.repo.id)

    def test_action_view_details_no_repo(self):
        """Test action_view_details raises UserError when no repository is linked."""
        project_no_repo = self.env['project.project'].create({'name': 'No Repo Project'})
        with self.assertRaises(UserError):
            project_no_repo.action_view_details()

    def test_action_view_github_repositories(self):
        """Test action_view_github_repositories returns a list window action."""
        result = self.project.action_view_github_repositories()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'github.repository')
        self.assertIn('list', result['view_mode'])

    def test_action_import_issues_no_repo(self):
        """Test action_import_issues_from_github raises UserError with no repo."""
        project_no_repo = self.env['project.project'].create({'name': 'Empty Project'})
        with self.assertRaises(UserError):
            project_no_repo.action_import_issues_from_github()

    def test_action_export_tasks_no_repo(self):
        """Test action_export_tasks_to_github raises UserError with no repo."""
        project_no_repo = self.env['project.project'].create({'name': 'Empty Project 2'})
        with self.assertRaises(UserError):
            project_no_repo.action_export_tasks_to_github()

    def test_action_export_tasks_no_unlinked_tasks(self):
        """Test action_export_tasks_to_github returns info notification when all tasks linked."""
        result = self.project.action_export_tasks_to_github()
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')

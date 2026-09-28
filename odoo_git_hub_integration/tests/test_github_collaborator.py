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
from odoo.exceptions import ValidationError


class TestGitHubCollaborator(TransactionCase):
    """Test cases for the GitHubCollaborator model (github.collaborator)."""

    def setUp(self):
        super().setUp()
        self.repo = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'testuser',
            'url': 'https://github.com/testuser/test-repo',
        })
        self.collaborator = self.env['github.collaborator'].create({
            'repository_id': self.repo.id,
            'github_id': 'gh_collab_001',
            'login': 'collaborator_one',
            'html_url': 'https://github.com/collaborator_one',
            'type': 'User',
        })

    def test_collaborator_creation(self):
        """Test that a collaborator record is created with correct data."""
        self.assertTrue(self.collaborator.id)
        self.assertEqual(self.collaborator.login, 'collaborator_one')
        self.assertEqual(self.collaborator.type, 'User')

    def test_collaborator_linked_to_repo(self):
        """Test that the collaborator is linked to the correct repository."""
        self.assertEqual(self.collaborator.repository_id.id, self.repo.id)

    def test_collaborator_unique_constraint(self):
        """Test that duplicate github_id per repository raises a constraint error."""
        constraints = [c[0] for c in self.env['github.collaborator']._sql_constraints]
        self.assertIn('github_id_repo_unique', constraints)

    def test_collaborator_rec_name(self):
        """Test the _rec_name is 'login' field."""
        self.assertEqual(self.collaborator.display_name, 'collaborator_one')

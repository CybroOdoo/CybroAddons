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

class TestGithubRepository(TransactionCase):
    """
    Test suite for the github.repository model.
    """
    
    def setUp(self):
        """
        Set up the test environment with a mock repository.
        """
        super(TestGithubRepository, self).setUp()
        self.repository = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'test-owner',
            'github_id': '12345'
        })

    def test_01_repository_creation(self):
        """Test basic repository creation"""
        self.assertTrue(self.repository.id)
        self.assertEqual(self.repository.name, 'test-repo')
        self.assertEqual(self.repository.owner, 'test-owner')

    def test_02_compute_counts(self):
        """Test compute functions for branches and collaborators"""
        branch = self.env['github.branch'].create({
            'repository_id': self.repository.id,
            'name': 'main'
        })
        collaborator = self.env['github.collaborator'].create({
            'repository_id': self.repository.id,
            'login': 'testuser',
            'github_id': 'user123'
        })
        self.repository._compute_branches_count()
        self.repository._compute_collaborators_count()
        self.assertEqual(self.repository.branches_count, 1)
        self.assertEqual(self.repository.collaborators_count, 1)

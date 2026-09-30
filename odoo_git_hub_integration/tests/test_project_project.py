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

class TestProjectProject(TransactionCase):
    """
    Test suite for the extended project.project model.
    """
    
    def setUp(self):
        """
        Set up the test environment with a mock repository and project.
        """
        super(TestProjectProject, self).setUp()
        self.repository = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'test-owner',
        })
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
            'github_repository_id': self.repository.id,
            'github_repository_ids': [(4, self.repository.id)]
        })

    def test_01_project_github_linking(self):
        """Test project linked to github repository"""
        self.assertEqual(self.project.github_repository_id, self.repository)
        self.assertIn(self.repository, self.project.github_repository_ids)

    def test_02_compute_counts(self):
        """Test compute functions for repositories"""
        self.project._compute_repositories_count()
        self.assertEqual(self.project.repositories_count, 1)

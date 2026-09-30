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

class TestGithubBranch(TransactionCase):
    """
    Test suite for the github.branch model.
    """
    
    def setUp(self):
        """
        Set up the test environment with a mock repository and branch.
        """
        super(TestGithubBranch, self).setUp()
        self.repository = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'test-owner',
            'github_id': '12345'
        })
        self.branch = self.env['github.branch'].create({
            'repository_id': self.repository.id,
            'name': 'test-branch',
            'is_default': True
        })

    def test_01_branch_creation(self):
        """Test branch creation"""
        self.assertEqual(self.branch.name, 'test-branch')
        self.assertTrue(self.branch.is_default)
        self.assertEqual(self.branch.repository_id, self.repository)

    def test_02_compute_commits_count(self):
        """Test compute commits count"""
        self.env['github.commit'].create({
            'repository_id': self.repository.id,
            'branch_id': self.branch.id,
            'sha': 'dummy_sha_123',
            'message': 'Test commit'
        })
        self.branch.compute_commits_count()
        self.assertEqual(self.branch.commits_count, 1)

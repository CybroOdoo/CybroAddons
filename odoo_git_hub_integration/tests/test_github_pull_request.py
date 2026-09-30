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

class TestGithubPullRequest(TransactionCase):
    """
    Test suite for the github.pull.request model.
    """
    
    def setUp(self):
        """
        Set up the test environment with a mock repository and pull request.
        """
        super(TestGithubPullRequest, self).setUp()
        self.repository = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'test-owner',
        })
        self.pr = self.env['github.pull.request'].create({
            'repository_id': self.repository.id,
            'github_id': 'pr-1',
            'title': 'Add new feature',
            'state': 'open',
            'head_branch': 'feature-branch',
            'base_branch': 'main'
        })

    def test_01_pr_creation(self):
        """Test PR creation"""
        self.assertEqual(self.pr.title, 'Add new feature')
        self.assertEqual(self.pr.state, 'open')
        self.assertEqual(self.pr.head_branch, 'feature-branch')
        self.assertEqual(self.pr.repository_id, self.repository)

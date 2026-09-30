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
from odoo import fields
from odoo.tests.common import TransactionCase

class TestGithubCommit(TransactionCase):
    """
    Test suite for the github.commit model.
    """
    
    def setUp(self):
        """
        Set up the test environment with a mock repository, branch, and commit.
        """
        super(TestGithubCommit, self).setUp()
        self.repository = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'test-owner',
        })
        self.branch = self.env['github.branch'].create({
            'repository_id': self.repository.id,
            'name': 'main',
        })
        self.commit = self.env['github.commit'].create({
            'repository_id': self.repository.id,
            'branch_id': self.branch.id,
            'sha': 'def456',
            'message': 'Fix bug #123',
            'author_name': 'Dev User',
            'committed_date': fields.Datetime.now()
        })

    def test_01_commit_creation(self):
        """Test commit creation"""
        self.assertEqual(self.commit.sha, 'def456')
        self.assertEqual(self.commit.message, 'Fix bug #123')
        self.assertEqual(self.commit.repository_id, self.repository)
        self.assertEqual(self.commit.branch_id, self.branch)

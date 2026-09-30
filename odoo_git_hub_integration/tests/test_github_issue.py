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
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase

class TestGithubIssue(TransactionCase):
    """
    Test suite for the github.issue model.
    """
    
    def setUp(self):
        """
        Set up the test environment with a mock repository and issue.
        """
        super(TestGithubIssue, self).setUp()
        self.repository = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'test-owner',
        })
        self.issue = self.env['github.issue'].create({
            'repository_id': self.repository.id,
            'github_id': 'issue-1',
            'title': 'Test Issue',
            'state': 'open',
            'created_at': fields.Datetime.now() - timedelta(days=2)
        })

    def test_01_issue_creation(self):
        """Test issue creation"""
        self.assertEqual(self.issue.title, 'Test Issue')
        self.assertEqual(self.issue.state, 'open')
        self.assertEqual(self.issue.repository_id, self.repository)

    def test_02_compute_issue_age(self):
        """Test computing issue age"""
        self.issue._compute_issue_age_days()
        self.assertEqual(self.issue.issue_age_days, 2)

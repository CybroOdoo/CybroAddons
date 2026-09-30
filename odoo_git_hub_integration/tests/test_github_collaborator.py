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

class TestGithubCollaborator(TransactionCase):
    """
    Test suite for the github.collaborator model.
    """
    
    def setUp(self):
        """
        Set up the test environment with a mock repository and collaborator.
        """
        super(TestGithubCollaborator, self).setUp()
        self.repository = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'test-owner',
        })
        self.collaborator = self.env['github.collaborator'].create({
            'repository_id': self.repository.id,
            'github_id': 'collab-1',
            'login': 'collab_user',
            'type': 'User'
        })

    def test_01_collaborator_creation(self):
        """Test collaborator creation"""
        self.assertEqual(self.collaborator.login, 'collab_user')
        self.assertEqual(self.collaborator.repository_id, self.repository)
        self.assertEqual(self.collaborator.github_id, 'collab-1')

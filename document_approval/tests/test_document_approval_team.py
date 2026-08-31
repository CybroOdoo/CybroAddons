# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import common

class TestDocumentApprovalTeam(common.TransactionCase):

    def setUp(self):
        super(TestDocumentApprovalTeam, self).setUp()
        self.team_model = self.env['document.approval.team']
        self.user = self.env.ref('base.user_admin')
        
    def test_team_creation(self):
        """Test creating a document approval team."""
        team = self.team_model.create({
            'name': 'Test Team',
            'team_lead_id': self.user.id,
            'is_active': True,
        })
        self.assertEqual(team.name, 'Test Team')
        self.assertEqual(team.team_lead_id, self.user)

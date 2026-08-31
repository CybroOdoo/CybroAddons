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
from odoo.exceptions import ValidationError, UserError

class TestDocumentApproval(common.TransactionCase):

    def setUp(self):
        super(TestDocumentApproval, self).setUp()
        self.approval_model = self.env['document.approval']
        self.team_model = self.env['document.approval.team']
        self.user = self.env.ref('base.user_admin')
        
        self.team = self.team_model.create({
            'name': 'Test Team',
            'team_lead_id': self.user.id,
            'step_ids': [(0, 0, {
                'steps': 1,
                'approver_id': self.user.id,
            })]
        })

    def test_approval_creation(self):
        """Test creating a document approval."""
        approval = self.approval_model.create({
            'name': 'Test Approval',
            'team_id': self.team.id,
        })
        self.assertEqual(approval.name, 'Test Approval')
        self.assertEqual(approval.state, 'draft')
        
    def test_check_team_member(self):
        """Test that creating an approval with a team without approvers raises a ValidationError."""
        team_without_approver = self.team_model.create({
            'name': 'Invalid Team',
            'team_lead_id': self.user.id,
        })
        with self.assertRaises(ValidationError):
            self.approval_model.create({
                'name': 'Invalid Approval',
                'team_id': team_without_approver.id,
            })
            
    def test_action_send_for_approval(self):
        """Test the send for approval action."""
        approval = self.approval_model.create({
            'name': 'Test Approval',
            'team_id': self.team.id,
        })
        approval.action_send_for_approval()
        self.assertEqual(approval.state, 'waiting')
        self.assertIn(self.user.id, approval.approver_ids.ids)
        
    def test_unlink_restrictions(self):
        """Test that unlinking an approval in approved or waiting state raises a UserError."""
        approval = self.approval_model.create({
            'name': 'Test Approval',
            'team_id': self.team.id,
        })
        approval.state = 'approved'
        with self.assertRaises(UserError):
            approval.unlink()
            
        approval.state = 'waiting'
        with self.assertRaises(UserError):
            approval.unlink()

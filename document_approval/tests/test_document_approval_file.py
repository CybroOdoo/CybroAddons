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
from odoo.exceptions import UserError
import base64

class TestDocumentApprovalFile(common.TransactionCase):

    def setUp(self):
        super(TestDocumentApprovalFile, self).setUp()
        self.file_model = self.env['document.approval.file']
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
        
        self.approval = self.approval_model.create({
            'name': 'Test Approval',
            'team_id': self.team.id,
            'state': 'draft'
        })
        
        self.file = self.file_model.create({
            'name': 'Test File',
            'file': base64.b64encode(b'Test content'),
            'approval_id': self.approval.id,
        })
        
    def test_unlink_file_draft(self):
        """Test deleting a file when the approval is in draft state."""
        self.file.unlink()
        self.assertFalse(self.file.exists())
        
    def test_unlink_file_not_draft(self):
        """Test that deleting a file when the approval is not in draft state raises an error."""
        self.approval.state = 'waiting'
        with self.assertRaises(UserError):
            self.file.unlink()

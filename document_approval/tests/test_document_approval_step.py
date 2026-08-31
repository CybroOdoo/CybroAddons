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

class TestDocumentApprovalStep(common.TransactionCase):

    def setUp(self):
        super(TestDocumentApprovalStep, self).setUp()
        self.step_model = self.env['document.approval.step']
        self.user = self.env.ref('base.user_admin')
        
    def test_step_creation(self):
        """Test creating a document approval step."""
        step = self.step_model.create({
            'steps': 1,
            'approver_id': self.user.id,
            'role': 'Manager',
        })
        self.assertEqual(step.steps, 1)
        self.assertEqual(step.approver_id, self.user)

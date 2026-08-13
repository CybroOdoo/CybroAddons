# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#   Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#   This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#   It is forbidden to publish, distribute, sublicense, or sell copies of the
#   Software or modified copies of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#   OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#   USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo.tests.common import TransactionCase
from odoo import fields

class TestApprovalRequest(TransactionCase):

    def setUp(self):
        super(TestApprovalRequest, self).setUp()
        self.category = self.env['approval.category'].create({
            'name': 'Sale Approval',
            'approval_type': 'sale',
            'approval_minimum': 0,
            'has_product': 'no',
        })
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.sale_order = self.env['sale.order'].create({'partner_id': self.partner.id})
        
        self.approval_request = self.env['approval.request'].create({
            'name': 'Test Request',
            'category_id': self.category.id,
            'order_id': self.sale_order.id,
        })
        # Add an approver
        self.approver = self.env['approval.approver'].create({
            'request_id': self.approval_request.id,
            'user_id': self.env.uid,
            'status': 'pending',
        })

    def test_01_action_approve(self):
        """Test action_approve function updating the sale order"""
        self.approver.status = 'approved'
        self.approval_request.action_approve()
        
        self.assertEqual(self.sale_order.state, 'approved')
        self.assertTrue(self.sale_order.is_approved)

    def test_02_action_refuse(self):
        """Test action_refuse function cancelling the sale order"""
        self.approval_request.action_refuse()
        self.assertEqual(self.sale_order.state, 'cancel')

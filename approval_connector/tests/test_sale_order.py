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

class TestSaleOrder(TransactionCase):

    def setUp(self):
        super(TestSaleOrder, self).setUp()
        # Clear existing sale categories to avoid interference from demo data
        self.env['approval.category'].search([('approval_type', '=', 'sale')]).write({'approval_type': 'purchase'})
        self.category = self.env['approval.category'].create({
            'name': 'Sale Approval',
            'approval_type': 'sale',
            'approval_minimum': 0,
            'has_product': 'no',
            'has_quantity': 'no',
            'has_amount': 'no',
            'has_period': 'no',
            'has_location': 'no',
            'has_payment_method': 'no',
        })
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({'name': 'Test Product', 'lst_price': 100.0})
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

    def test_01_can_be_confirmed(self):
        """Test _can_be_confirmed function for new states"""
        self.sale_order.state = 'draft'
        self.assertTrue(self.sale_order._can_be_confirmed())
        self.sale_order.state = 'approved'
        self.assertTrue(self.sale_order._can_be_confirmed())
        self.sale_order.state = 'approve'
        self.assertFalse(self.sale_order._can_be_confirmed())

    def test_02_action_confirm_with_approval(self):
        """Test action_confirm logic triggering approval request"""
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.state, 'approve')
        
        request = self.env['approval.request'].search([('order_id', '=', self.sale_order.id)])
        self.assertTrue(request, "Approval request should have been created")
        self.assertEqual(request.category_id, self.category)

    def test_03_action_confirm_bypass(self):
        """Test action_confirm bypass logic"""
        self.category.approval_type = 'purchase'
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.state, 'sale', "Should bypass and confirm")

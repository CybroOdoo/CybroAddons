# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo.addons.mail.tests.common import new_test_user
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestApprovalConnector(TransactionCase):
    """Tests for the sale order approval flow"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env.ref(
            'approval_connector.approval_category_data_sale')
        cls.approver = new_test_user(
            cls.env, login='approval_connector_approver',
            groups='base.group_user,approvals.group_approval_user,'
                   'sales_team.group_sale_manager')
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.product = cls.env['product.product'].create(
            {'name': 'Test Product', 'list_price': 10})

    def _create_order(self, **values):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })],
            **values,
        })

    def _add_approver(self):
        self.category.write({'approver_ids': [(0, 0, {
            'user_id': self.approver.id,
            'required': True,
        })]})

    def test_confirm_without_approvers(self):
        """The default category has no approvers, so confirmation works"""
        order = self._create_order()
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_confirm_requests_approval(self):
        """Confirming creates an approval request and waits for it"""
        self._add_approver()
        order = self._create_order()
        order.action_confirm()
        self.assertEqual(order.state, 'approve')
        request = self.env['approval.request'].search(
            [('order_id', '=', order.id)])
        self.assertEqual(len(request), 1)
        self.assertEqual(request.category_id, self.category)

    def test_confirm_multiple_orders(self):
        """Confirming several orders at once creates one request each"""
        self._add_approver()
        orders = self._create_order() | self._create_order()
        orders.action_confirm()
        self.assertEqual(orders.mapped('state'), ['approve', 'approve'])
        requests = self.env['approval.request'].search(
            [('order_id', 'in', orders.ids)])
        self.assertEqual(requests.mapped('order_id'), orders)

    def test_request_owner_without_salesperson(self):
        """The request owner falls back to the current user"""
        self._add_approver()
        order = self._create_order(user_id=False)
        order.action_confirm()
        request = self.env['approval.request'].search(
            [('order_id', '=', order.id)])
        self.assertEqual(request.request_owner_id, self.env.user)

    def test_approve_then_confirm(self):
        """An approved order can then be confirmed"""
        self._add_approver()
        order = self._create_order()
        order.action_confirm()
        request = self.env['approval.request'].search(
            [('order_id', '=', order.id)])
        request.with_user(self.approver).action_approve()
        self.assertEqual(order.state, 'approved')
        self.assertTrue(order.is_approved)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_refuse_cancels_order(self):
        """A refused request cancels the sale order"""
        self._add_approver()
        order = self._create_order()
        order.action_confirm()
        request = self.env['approval.request'].search(
            [('order_id', '=', order.id)])
        request.with_user(self.approver).action_refuse()
        self.assertEqual(order.state, 'cancel')

    def test_refuse_multiple_requests(self):
        """Refusing several requests at once cancels every order"""
        self._add_approver()
        orders = self._create_order() | self._create_order()
        orders.action_confirm()
        requests = self.env['approval.request'].search(
            [('order_id', 'in', orders.ids)])
        requests.with_user(self.approver).action_refuse()
        self.assertEqual(orders.mapped('state'), ['cancel', 'cancel'])

    def test_redraft_resets_approval(self):
        """A re-drafted order has to be approved again"""
        self._add_approver()
        order = self._create_order()
        order.action_confirm()
        request = self.env['approval.request'].search(
            [('order_id', '=', order.id)])
        request.with_user(self.approver).action_approve()
        order.action_cancel()
        order.action_draft()
        self.assertFalse(order.is_approved)
        order.action_confirm()
        self.assertEqual(order.state, 'approve')

    def test_copy_does_not_keep_approval(self):
        """A duplicated order does not inherit the approval"""
        order = self._create_order()
        order.is_approved = True
        self.assertFalse(order.copy().is_approved)

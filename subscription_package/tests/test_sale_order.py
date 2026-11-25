# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
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
#############################################################################
from odoo.tests.common import TransactionCase

class TestSaleOrder(TransactionCase):
    """Test Sale Order Model"""

    def setUp(self):
        """Setup test variables"""
        super(TestSaleOrder, self).setUp()
        self.SaleOrder = self.env['sale.order']
        self.Partner = self.env['res.partner']
        self.partner = self.Partner.create({'name': 'Test Partner'})
        self.plan = self.env['subscription.package.plan'].create({
            'name': 'Plan A',
            'renewal_value': '1',
            'renewal_period': 'months'
        })
        self.product = self.env['product.product'].create({
            'name': 'Sub Product', 
            'is_subscription': True,
            'subscription_plan_id': self.plan.id
        })
        self.env['subscription.package.stage'].create({'name': 'Draft', 'category': 'draft'})
        self.env['subscription.package.stage'].create({'name': 'In Progress', 'category': 'progress'})

    def test_action_confirm_creates_subscription(self):
        """Test that confirming a sale order with subscription products creates a subscription package"""
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0
            })]
        })
        
        # Odoo 19 private _action_confirm is called during action_confirm
        order.action_confirm()
        
        # Verify subscription was created
        sub = self.env['subscription.package'].search([('sale_order_id', '=', order.id)])
        self.assertEqual(len(sub), 1)
        self.assertEqual(sub.partner_id, self.partner)
        self.assertEqual(sub.plan_id, self.plan)

    def test_action_confirm_updates_existing_subscription(self):
        """Test that confirming an order linked to an existing subscription updates its stage"""
        sub = self.env['subscription.package'].create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'product_line_ids': [(0, 0, {'product_id': self.product.id})]
        })
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'subscription_id': sub.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0
            })]
        })
        sub.sale_order_id = order
        
        order.action_confirm()
        
        # Verify subscription stage moved to progress
        self.assertEqual(sub.stage_id.category, 'progress')
        self.assertTrue(sub.start_date)

    def test_multi_record_create(self):
        """Test multi-record creation of sale orders"""
        sub = self.env['subscription.package'].create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'reference_code': 'REF-123',
            'product_line_ids': [(0, 0, {'product_id': self.product.id})]
        })
        orders = self.SaleOrder.create([
            {
                'partner_id': self.partner.id,
                'subscription_id': sub.id,
            },
            {
                'partner_id': self.partner.id,
            }
        ])
        self.assertEqual(len(orders), 2)
        self.assertTrue(orders[0].is_subscription)
        self.assertEqual(orders[0].sub_reference, 'REF-123')
        self.assertFalse(orders[1].is_subscription)

    def test_button_subscription_and_count(self):
        """Test button_subscription action and subscription count"""
        sub = self.env['subscription.package'].create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'product_line_ids': [(0, 0, {'product_id': self.product.id})],
        })
        order = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'subscription_id': sub.id,
        })
        sub.sale_order_id = order
        order._compute_subscription_count()
        self.assertEqual(order.subscription_count, 1)
        action = order.button_subscription()
        self.assertEqual(action['res_model'], 'subscription.package')

    def test_sale_order_line_compute_qty_to_invoice(self):
        """Test _compute_qty_to_invoice for subscription and non-subscription lines"""
        sub = self.env['subscription.package'].create({
            'partner_id': self.partner.id,
            'plan_id': self.plan.id,
            'product_line_ids': [(0, 0, {'product_id': self.product.id})],
            'is_closed': False,
        })
        # 1. Subscription active line
        so_sub = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'subscription_id': sub.id,
            'is_subscription': True,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
                'price_unit': 100.0,
            })]
        })
        line_sub = so_sub.order_line[0]
        line_sub._compute_qty_to_invoice()
        self.assertEqual(line_sub.qty_to_invoice, 5)

        # 2. Standard product with invoice_policy = 'order' confirmed
        standard_prod_order = self.env['product.product'].create({
            'name': 'Standard Prod Order',
            'invoice_policy': 'order',
        })
        so_normal = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': standard_prod_order.id,
                'product_uom_qty': 4,
                'price_unit': 50.0,
            })]
        })
        line_normal = so_normal.order_line[0]
        # In draft, qty_to_invoice should be 0
        line_normal._compute_qty_to_invoice()
        self.assertEqual(line_normal.qty_to_invoice, 0)

        # Confirm order
        so_normal.action_confirm()
        line_normal._compute_qty_to_invoice()
        self.assertEqual(line_normal.qty_to_invoice, 4)

        # 3. Standard product with invoice_policy = 'delivery' confirmed
        standard_prod_del = self.env['product.product'].create({
            'name': 'Standard Prod Delivery',
            'invoice_policy': 'delivery',
        })
        so_del = self.SaleOrder.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': standard_prod_del.id,
                'product_uom_qty': 10,
                'price_unit': 20.0,
            })]
        })
        so_del.action_confirm()
        line_del = so_del.order_line[0]
        line_del.qty_delivered = 6
        line_del._compute_qty_to_invoice()
        self.assertEqual(line_del.qty_to_invoice, 6)

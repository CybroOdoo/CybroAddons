# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#     Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author: Anaswara S (odoo@cybrosys.com)
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
from odoo.tests import common
from odoo.exceptions import ValidationError

class TestLaundryOrder(common.TransactionCase):

    def setUp(self):
        super(TestLaundryOrder, self).setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test Laundry User',
            'login': 'test_laundry_user_order',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
            'type': 'contact'
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Dress',
            'type': 'service'
        })
        
        self.washing_type = self.env['washing.type'].create({
            'name': 'Dry Clean',
            'assigned_person_id': self.user.id,
            'amount': 200.0,
        })
        self.washing_work = self.env['washing.work'].create({
            'name': 'Perfume',
            'assigned_person_id': self.user.id,
            'amount': 50.0,
        })

    def test_laundry_order_flow(self):
        """Test the full flow of laundry.order"""
        order = self.env['laundry.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'laundry_person_id': self.user.id,
            'order_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'qty': 2,
                'washing_type_id': self.washing_type.id,
                'extra_work_ids': [(6, 0, [self.washing_work.id])]
            })]
        })
        
        # Test default states
        self.assertEqual(order.state, 'draft')
        
        # Test computation of amount in line and total
        line = order.order_line_ids[0]
        self.assertEqual(line.amount, 500.0)
        self.assertEqual(order.total_amount, 500.0)
        
        # Test confirm order
        order.confirm_order()
        self.assertEqual(order.state, 'order')
        self.assertTrue(order.sale_id)
        self.assertEqual(order.sale_id.partner_id.id, self.partner.id)
        
        # Test work count and view works
        order._compute_work_count()
        self.assertEqual(order.work_count, 1)
        action = order.action_view_laundry_works()
        self.assertEqual(action.get('res_model'), 'washing.washing')
        
        # Test return dress
        order.action_return_dress()
        self.assertEqual(order.state, 'return')
        
        # Test cancel
        order.action_cancel_order()
        self.assertEqual(order.state, 'cancel')

    def test_laundry_order_unlink(self):
        order = self.env['laundry.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'laundry_person_id': self.user.id,
            'order_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'qty': 1,
                'washing_type_id': self.washing_type.id,
            })]
        })
        order.action_return_dress()
        
        admin_group = self.env.ref('laundry_management.group_laundry_admin', raise_if_not_found=False)
        if admin_group:
            admin_group.write({'user_ids': [(4, self.user.id)]})
        
        with self.assertRaises(ValidationError):
            order.with_user(self.user).unlink()

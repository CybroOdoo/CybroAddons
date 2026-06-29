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

class TestWashingWashing(common.TransactionCase):

    def setUp(self):
        super(TestWashingWashing, self).setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test Laundry User',
            'login': 'test_laundry_user_washing',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Dress',
            'type': 'service',
            'list_price': 100.0,
        })
        self.uom = self.env.ref('uom.product_uom_unit')
        
        self.washing_type = self.env['washing.type'].create({
            'name': 'Dry Clean',
            'assigned_person_id': self.user.id,
            'amount': 200.0,
        })
        
        self.laundry_order = self.env['laundry.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'laundry_person_id': self.user.id,
            'order_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'qty': 2,
                'washing_type_id': self.washing_type.id,
            })]
        })
        self.laundry_order.confirm_order()
        self.laundry_line = self.laundry_order.order_line_ids[0]

    def test_washing_flow(self):
        """Test the full flow of washing.washing"""
        wash = self.env['washing.washing'].search([('laundry_id', '=', self.laundry_line.id)], limit=1)
        self.assertTrue(wash)
        
        # Add products to wash
        wash.write({
            'product_line_ids': [(0, 0, {
                'name': 'Detergent',
                'uom_id': self.uom.id,
                'quantity': 2,
                'product_id': self.product.id,
            })]
        })
        
        # Test compute total amount
        line = wash.product_line_ids[0]
        self.assertEqual(line.subtotal, 200.0)
        self.assertEqual(wash.total_amount, 200.0)
        
        # Test start wash
        wash.start_wash()
        self.assertEqual(wash.state, 'process')
        self.assertEqual(self.laundry_line.state, 'wash')
        self.assertEqual(self.laundry_order.state, 'process')
        
        # Test done
        wash.action_set_to_done()
        self.assertEqual(wash.state, 'done')
        self.assertEqual(self.laundry_line.state, 'done')
        self.assertEqual(self.laundry_order.state, 'done')

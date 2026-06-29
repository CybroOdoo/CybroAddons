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

class TestSaleAdvancePayment(common.TransactionCase):

    def setUp(self):
        super(TestSaleAdvancePayment, self).setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test Laundry User',
            'login': 'test_laundry_user_payment',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Dress',
            'type': 'service',
            'invoice_policy': 'order'
        })
        
        self.laundry_service_product = self.env.ref('laundry_management.product_product_laundry_service', raise_if_not_found=False)
        if self.laundry_service_product:
            self.laundry_service_product.write({'invoice_policy': 'order'})
        
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

    def test_create_invoices(self):
        """Test invoice creation from laundry sale order"""
        sale_order = self.laundry_order.sale_id
        sale_order.action_confirm()
        
        adv_payment = self.env['sale.advance.payment.inv'].with_context(
            laundry_sale_id=[sale_order.id]
        ).create({
            'advance_payment_method': 'delivered',
        })
        
        result = adv_payment.create_invoices()
        self.assertTrue(result)
        
        # The invoice count should be 1
        self.laundry_order._compute_invoice_count()
        self.assertEqual(self.laundry_order.invoice_count, 1)

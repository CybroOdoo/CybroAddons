# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Deepika V(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase, tagged
from unittest.mock import patch, MagicMock

@tagged('post_install', '-at_install')
class TestSaleOrderInvoiceDetail(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrderInvoiceDetail, cls).setUpClass()
        
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner'
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                })
            ]
        })
        cls.sale_order.action_confirm()
        cls.product.invoice_policy = 'order'
        cls.invoice = cls.sale_order._create_invoices()
        cls.invoice.name = 'INV/TEST/0001'

    def test_compute_invoice_amount(self):
        """Test the computation of invoiced, paid, and due amounts."""
        
        self.sale_order._compute_invoice_amount()
        expected_total = self.invoice.amount_total
        self.assertEqual(self.sale_order.invoiced_amount, expected_total)
        self.assertEqual(self.sale_order.paid_amount, 0.0)
        self.assertEqual(self.sale_order.due_amount, expected_total)
        self.assertEqual(self.sale_order.payment_count, 0)
        PaymentModelClass = type(self.env['account.payment'])
        
        with patch.object(PaymentModelClass, 'search') as mock_search:
            mock_payments = MagicMock()
            mock_payments.mapped.return_value = [40.0]
            mock_payments.__len__.return_value = 1
            mock_search.return_value = mock_payments
            
            self.sale_order._compute_invoice_amount()
            
            self.assertEqual(self.sale_order.paid_amount, 40.0)
            self.assertEqual(self.sale_order.payment_count, 1)
            self.assertEqual(self.sale_order.due_amount, expected_total - 40.0)

    def test_compute_paid_amount_percent(self):
        """Test paid amount percentage calculation."""
        self.sale_order.amount_total = 200.0
        self.sale_order.paid_amount = 50.0
        
        self.sale_order._compute_paid_amount_percent()
        
        self.assertEqual(self.sale_order.paid_amount_percent, 25.0, "Paid amount percent should be 25%")
        self.sale_order.amount_total = 0.0
        self.sale_order.paid_amount = 50.0
        self.sale_order._compute_paid_amount_percent()
        self.assertEqual(self.sale_order.paid_amount_percent, 0.0, "Should handle division by zero and return 0.0")

    def test_action_view_payments(self):
        """Test action returning the payments of the order."""
        payment = self.env['account.payment'].create({
            'amount': 40.0,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner.id,
            'memo': 'INV/TEST/0001',
        })
        
        action = self.sale_order.action_view_payments()
        
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.payment')
        self.assertIn(('id', 'in', [payment.id]), action['domain'])

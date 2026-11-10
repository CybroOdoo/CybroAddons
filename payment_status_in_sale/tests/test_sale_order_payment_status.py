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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderPaymentStatus(TransactionCase):
    """Unit test suite for Sale Order Payment Status and payment details."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Payment Customer',
            'email': 'customer@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Service Product',
            'type': 'service',
            'list_price': 150.0,
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 150.0,
                }),
            ],
        })

    def test_01_no_invoice_initial_state(self):
        """Test initial status when no invoice is linked to the sale order."""
        self.order._compute_payment_status()
        self.order._compute_invoice_state()
        self.order._compute_amount_due()
        self.order._compute_payment_details()

        self.assertEqual(self.order.payment_status, 'No invoice')
        self.assertEqual(self.order.invoice_state, 'No invoice')
        self.assertEqual(self.order.amount_due, 0.0)
        self.assertFalse(self.order.payment_details)

    def test_02_draft_invoice_state(self):
        """Test invoice state and payment status when an invoice is in draft."""
        self.order.action_confirm()
        invoice = self.order._create_invoices()

        self.assertEqual(self.order.invoice_state, 'draft')
        self.assertEqual(self.order.payment_status, 'No invoice')
        self.assertEqual(self.order.amount_due, 0.0)

    def test_03_posted_invoice_not_paid(self):
        """Test status transitions when the invoice is confirmed and posted."""
        self.order.action_confirm()
        invoice = self.order._create_invoices()
        invoice.action_post()

        self.order._compute_payment_status()
        self.order._compute_invoice_state()
        self.order._compute_amount_due()

        self.assertEqual(self.order.invoice_state, 'posted')
        self.assertEqual(self.order.payment_status, 'Not Paid')
        self.assertGreater(self.order.amount_due, 0.0)

    def test_04_action_register_payment(self):
        """Test the Register Payment action opens the payment register wizard."""
        self.order.action_confirm()
        invoice = self.order._create_invoices()
        invoice.action_post()

        action = self.order.action_register_payment()
        self.assertEqual(action.get('res_model'), 'account.payment.register')
        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('context', {}).get('active_model'), 'account.move')
        self.assertIn(invoice.id, action.get('context', {}).get('active_ids', []))

    def test_05_action_open_business_doc(self):
        """Test action_open_business_doc handles non-existing move safely."""
        res = self.order.action_open_business_doc()
        self.assertFalse(res)

    def test_06_compute_payment_details_and_states(self):
        """Test payment details compute and status variations directly."""
        self.order.action_confirm()
        invoice = self.order._create_invoices()

        invoice.invoice_payments_widget = {
            'content': [
                {
                    'name': 'Customer Payment 001',
                    'amount': 100.0,
                    'date': '2026-11-09',
                }
            ]
        }
        self.order._compute_payment_details()
        self.assertTrue(self.order.payment_details)
        self.assertIn('content', self.order.payment_details)
        self.assertEqual(len(self.order.payment_details['content']), 1)

    def test_07_amount_due_with_credit_notes(self):
        """Test amount due computation when credit note is present."""
        self.order.action_confirm()
        invoice = self.order._create_invoices()
        invoice.action_post()

        initial_due = self.order.amount_due
        self.assertGreater(initial_due, 0.0)

        credit_note = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'price_unit': 50.0,
                }),
            ],
        })
        credit_note.action_post()
        self.order.invoice_ids = [(4, credit_note.id)]
        self.order._compute_amount_due()

        self.assertLess(self.order.amount_due, initial_due)

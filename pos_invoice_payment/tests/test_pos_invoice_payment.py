# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
################################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPosInvoicePayment(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        """Setup test data for POS invoice payment tests."""
        super(TestPosInvoicePayment, cls).setUpClass()
        # Create a partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        # Create a product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
            'list_price': 100.0,
        })
        # Create a draft invoice
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })

    def test_01_get_invoices(self):
        """Test getting invoices from the model."""
        invoices = self.env['account.move'].get_invoices()
        # Check if our created invoice is in the list
        invoice_ids = [inv['invoice_id'] for inv in invoices]
        self.assertIn(self.invoice.id, invoice_ids, "The created invoice should be in the returned list.")

    def test_02_post_invoice(self):
        """Test posting an invoice."""
        self.assertEqual(self.invoice.state, 'draft', "Invoice should be in draft state initially.")
        self.env['account.move'].post_invoice(self.invoice.id)
        self.assertEqual(self.invoice.state, 'posted', "Invoice should be in posted state after method call.")

    def test_03_register_payment(self):
        """Test registering payment for an invoice."""
        # Ensure invoice is posted first
        self.invoice.action_post()
        self.assertEqual(self.invoice.payment_state, 'not_paid', "Invoice should be unpaid.")
        
        # Register payment
        self.env['account.move'].register_payment(self.invoice.id)
        
        # In Odoo 18, payment state might be 'in_payment' or 'paid' depending on reconciliation
        self.assertIn(self.invoice.payment_state, ['in_payment', 'paid'], "Invoice should be in_payment or paid.")

    def test_04_create_payment(self):
        """Test creating a generic payment for a partner."""
        # Find a journal
        journal = self.env['account.journal'].search([('type', 'in', ['bank', 'cash'])], limit=1)
        self.assertTrue(journal, "No bank or cash journal found for testing.")
        
        payment_vals = {
            'journal_id': journal.id,
            'partner_id': self.partner.id,
            'currency_id': self.env.company.currency_id.id,
            'amount': 50.0,
        }
        
        # Initial payment count
        initial_count = self.env['account.payment'].search_count([('partner_id', '=', self.partner.id)])
        
        # Create payment
        self.env['account.payment'].create_payment(payment_vals)
        
        # New payment count
        new_count = self.env['account.payment'].search_count([('partner_id', '=', self.partner.id)])
        self.assertEqual(new_count, initial_count + 1, "A new payment should have been created.")
        
        # Check if the payment is posted
        payment = self.env['account.payment'].search([('partner_id', '=', self.partner.id)], order='id desc', limit=1)
        self.assertIn(payment.state, ['posted', 'in_process'], "The created payment should be in posted or in_process state.")

    def test_05_get_journal(self):
        """Test getting available journals."""
        journals = self.env['account.journal'].get_journal()
        self.assertTrue(len(journals) > 0, "At least one journal should be returned.")
        for journal in journals:
            self.assertIn('id', journal)
            self.assertIn('name', journal)
            journal_obj = self.env['account.journal'].browse(journal['id'])
            self.assertIn(journal_obj.type, ['bank', 'cash'], "Journal type should be bank or cash.")

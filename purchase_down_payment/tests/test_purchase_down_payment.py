# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestPurchaseDownPayment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set up a testing environment
        cls.partner = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'standard_price': 100.0,
            'list_price': 150.0,
            'purchase_method': 'receive',
        })
        # Create a basic Purchase Order
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'name': cls.product.name,
                'product_qty': 10.0,
                'price_unit': 100.0,
                'product_uom': cls.product.uom_po_id.id,
            })],
        })
        cls.purchase_order.button_confirm()

    def test_fixed_amount_down_payment(self):
        """Test creating a fixed amount down payment"""
        wizard = self.env['purchase.order.advance.payment'].with_context(active_ids=self.purchase_order.ids, active_model='purchase.order', active_id=self.purchase_order.id).create({
            'advance_payment_method': 'fixed',
            'fixed_amount': 200.0,
        })
        
        wizard.action_create_advance_bill()
        
        # Check that a down payment product was created and used
        down_payment_product = self.env['ir.config_parameter'].sudo().get_param('purchase_down_payment.po_deposit_default_product_id')
        self.assertTrue(down_payment_product, "Down payment default product parameter should be set.")
        
        # Check that a new order line for the down payment was added to the PO
        down_payment_line = self.purchase_order.order_line.filtered(lambda l: l.is_downpayment)
        self.assertTrue(down_payment_line, "A down payment line should have been added to the purchase order.")
        self.assertEqual(down_payment_line.price_unit, 200.0, "Down payment line price should match the fixed amount.")

    def test_percentage_down_payment(self):
        """Test creating a percentage down payment"""
        # 10 * 100 = 1000 total. 20% down payment = 200.
        wizard = self.env['purchase.order.advance.payment'].with_context(active_ids=self.purchase_order.ids, active_model='purchase.order', active_id=self.purchase_order.id).create({
            'advance_payment_method': 'percentage',
            'amount': 20.0,
        })
        
        wizard.action_create_advance_bill()
        
        down_payment_line = self.purchase_order.order_line.filtered(lambda l: l.is_downpayment)
        self.assertTrue(down_payment_line, "A down payment line should have been added to the purchase order.")
        self.assertEqual(down_payment_line.price_unit, 200.0, "Down payment line price should match the calculated percentage amount.")

    def test_deduct_down_payment_regular_bill(self):
        """Test deducting the down payment from the regular bill"""
        # Create a fixed down payment first
        wizard = self.env['purchase.order.advance.payment'].with_context(active_ids=self.purchase_order.ids, active_model='purchase.order', active_id=self.purchase_order.id).create({
            'advance_payment_method': 'fixed',
            'fixed_amount': 300.0,
        })
        wizard.action_create_advance_bill()
        
        # Receive the products
        self.purchase_order.order_line[0].qty_received = 10.0
        
        # Create regular bill and deduct down payments
        wizard_deduct = self.env['purchase.order.advance.payment'].with_context(active_ids=self.purchase_order.ids, active_model='purchase.order', active_id=self.purchase_order.id).create({
            'advance_payment_method': 'delivered',
            'deduct_down_payments': True,
        })
        
        # We need to simulate the action_create_advance_bill for deduction which ultimately creates an invoice
        action_result = wizard_deduct.action_create_advance_bill()
        
        # Find the latest bill (vendor bill)
        invoices = self.purchase_order.invoice_ids
        self.assertTrue(invoices, "Invoices should be generated.")
        
        # The regular invoice should have lines for the product and a negative line for the down payment
        regular_invoice = invoices.sorted(key=lambda i: i.id)[-1]
        down_payment_invoice_line = regular_invoice.invoice_line_ids.filtered(lambda l: l.is_downpayment)
        self.assertTrue(down_payment_invoice_line, "The down payment should be deducted in the regular invoice.")
        self.assertEqual(down_payment_invoice_line.quantity, -1.0, "The deducted down payment line should have a negative quantity.")

    def test_negative_down_payment_validation(self):
        """Test that negative down payment values raise UserError"""
        wizard = self.env['purchase.order.advance.payment'].with_context(active_ids=self.purchase_order.ids, active_model='purchase.order', active_id=self.purchase_order.id).create({
            'advance_payment_method': 'fixed',
            'fixed_amount': -50.0,
        })
        
        with self.assertRaises(UserError):
            wizard.action_create_advance_bill()

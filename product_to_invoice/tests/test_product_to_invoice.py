# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

"""Automated tests for Add Multiple Products To Invoice/Bill."""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductToInvoice(TransactionCase):
    """Test product selection, wizard and invoice-line creation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Test Customer/Vendor',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product To Invoice',
            'type': 'consu',
            'list_price': 125.0,
            'standard_price': 80.0,
        })
        cls.customer_invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner_a.id,
        })
        cls.vendor_bill = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': cls.partner_a.id,
        })

    def test_add_products_action_opens_product_view(self):
        action = self.customer_invoice.action_add_product()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'product.product')
        self.assertEqual(action['view_mode'], 'kanban,list,form')
        self.assertTrue(action['context']['add_to_invoice'])

    def test_add_to_invoice_context_flag(self):
        product = self.product.with_context(add_to_invoice=True)
        self.assertTrue(product.add_to_invoice)
        self.assertFalse(self.product.with_context(
            add_to_invoice=False).add_to_invoice)

    def test_change_qty_opens_details_wizard(self):
        action = self.product.with_context(
            active_id=self.customer_invoice.id
        ).action_change_qty()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'invoice.product.details')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['default_account_move_id'],
                         self.customer_invoice.id)
        self.assertEqual(action['context']['default_product_id'], self.product.id)
        self.assertEqual(action['context']['default_price_unit'],
                         self.product.lst_price)

    def test_change_qty_uses_cost_for_vendor_bill(self):
        action = self.product.with_context(
            active_id=self.vendor_bill.id
        ).action_change_qty()
        self.assertEqual(action['context']['default_price_unit'],
                         self.product.standard_price)

    def test_wizard_adds_product_to_customer_invoice(self):
        wizard = self.env['invoice.product.details'].create({
            'product_id': self.product.id,
            'account_move_id': self.customer_invoice.id,
            'qty': 3.0,
            'price_unit': 110.0,
        })
        wizard.action_add_to_invoice()
        lines = self.customer_invoice.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product
        )
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.quantity, 3.0)
        self.assertEqual(lines.price_unit, 110.0)

    def test_product_action_adds_sales_price_to_customer_invoice(self):
        self.product.with_context(
            active_id=self.customer_invoice.id
        ).action_add_to_invoice()
        lines = self.customer_invoice.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product
        )
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.quantity, 1.0)
        self.assertEqual(lines.price_unit, self.product.lst_price)

    def test_product_action_adds_cost_price_to_vendor_bill(self):
        self.product.with_context(
            active_id=self.vendor_bill.id).action_add_to_invoice()
        lines = self.vendor_bill.invoice_line_ids.filtered(
            lambda line: line.product_id == self.product
        )
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.quantity, 1.0)
        self.assertEqual(lines.price_unit, self.product.standard_price)

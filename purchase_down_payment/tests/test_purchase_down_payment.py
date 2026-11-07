# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#
################################################################################
"""Unit tests for purchase_down_payment module."""
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'purchase_down_payment')
class TestPurchaseDownPayment(TransactionCase):
    """Test suite covering purchase order down payments and deduction."""

    # pylint: disable=protected-access

    @classmethod
    def setUpClass(cls):
        """Prepare sample vendor, products, and purchase orders."""
        super().setUpClass()
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor Down Payment',
        })
        cls.deposit_product = cls.env['product.product'].create({
            'name': 'Down Payment Deposit Product',
            'type': 'service',
            'purchase_method': 'purchase',
            'supplier_taxes_id': False,
        })
        cls.env['ir.config_parameter'].sudo().set_int(
            'purchase_down_payment.po_deposit_default_product_id',
            cls.deposit_product.id,
        )
        cls.product = cls.env['product.product'].create({
            'name': 'Test Consumable Product',
            'type': 'consu',
            'purchase_method': 'purchase',
            'supplier_taxes_id': False,
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_qty': 10.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        cls.po.button_confirm()

    def test_wizard_defaults(self):
        """Verify default values computed on the advance payment wizard."""
        wizard = self.env['purchase.order.advance.payment'].with_context(
            active_model='purchase.order',
            active_id=self.po.id,
            active_ids=self.po.ids,
        ).new({})
        self.assertEqual(wizard.currency_id, self.po.currency_id)
        self.assertEqual(wizard.product_id, self.deposit_product)
        self.assertFalse(wizard.has_down_payments)

    def test_fixed_down_payment_and_deduction(self):
        """Verify fixed down payment creation and its deduction."""
        ctx = {
            'active_model': 'purchase.order',
            'active_id': self.po.id,
            'active_ids': self.po.ids,
        }
        wizard = self.env['purchase.order.advance.payment'].with_context(
            **ctx
        ).create({
            'advance_payment_method': 'fixed',
            'fixed_amount': 250.0,
            'product_id': self.deposit_product.id,
        })
        wizard.action_create_advance_bill()

        downpayment_lines = self.po.order_line.filtered(
            lambda line: line.is_downpayment
        )
        self.assertTrue(downpayment_lines)
        self.assertEqual(downpayment_lines.price_unit, 250.0)

        bills = self.po.invoice_ids
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills.amount_total, 250.0)

        # Create final bill deducting down payments
        wizard_deduct = self.env[
            'purchase.order.advance.payment'
        ].with_context(**ctx).create({
            'advance_payment_method': 'delivered',
            'deduct_down_payments': True,
        })
        wizard_deduct.action_create_advance_bill()

        all_bills = self.po.invoice_ids
        self.assertEqual(len(all_bills), 2)
        final_bill = all_bills - bills
        self.assertEqual(final_bill.amount_total, 750.0)

    def test_percentage_down_payment(self):
        """Verify percentage based down payment calculation."""
        po2 = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 5.0,
                    'price_unit': 200.0,
                }),
            ],
        })
        po2.button_confirm()

        ctx = {
            'active_model': 'purchase.order',
            'active_id': po2.id,
            'active_ids': po2.ids,
        }
        wizard = self.env['purchase.order.advance.payment'].with_context(
            **ctx
        ).create({
            'advance_payment_method': 'percentage',
            'amount': 20.0,
            'product_id': self.deposit_product.id,
        })
        wizard.action_create_advance_bill()

        dp_lines = po2.order_line.filtered(lambda line: line.is_downpayment)
        self.assertTrue(dp_lines)
        self.assertEqual(dp_lines.price_unit, 200.0)
        self.assertEqual(po2.invoice_ids.amount_total, 200.0)


    def test_validation_negative_or_zero_amount(self):
        """Verify error raised on negative or zero down payment."""
        ctx = {
            'active_model': 'purchase.order',
            'active_id': self.po.id,
            'active_ids': self.po.ids,
        }
        wizard_zero_fixed = self.env[
            'purchase.order.advance.payment'
        ].with_context(**ctx).create({
            'advance_payment_method': 'fixed',
            'fixed_amount': 0.0,
            'product_id': self.deposit_product.id,
        })
        with self.assertRaises(UserError):
            wizard_zero_fixed.action_create_advance_bill()

        wizard_zero_pct = self.env[
            'purchase.order.advance.payment'
        ].with_context(**ctx).create({
            'advance_payment_method': 'percentage',
            'amount': -5.0,
            'product_id': self.deposit_product.id,
        })
        with self.assertRaises(UserError):
            wizard_zero_pct.action_create_advance_bill()

    def test_validation_deposit_product_type_and_purchase_method(self):
        """Verify error raised on invalid deposit product type or purchase method."""
        ctx = {
            'active_model': 'purchase.order',
            'active_id': self.po.id,
            'active_ids': self.po.ids,
        }
        product_received = self.env['product.product'].create({
            'name': 'Invalid Method Product',
            'type': 'service',
            'purchase_method': 'receive',
        })
        wizard_invalid_method = self.env[
            'purchase.order.advance.payment'
        ].with_context(**ctx).create({
            'advance_payment_method': 'fixed',
            'fixed_amount': 50.0,
            'product_id': product_received.id,
        })
        with self.assertRaises(UserError):
            wizard_invalid_method.action_create_advance_bill()

        product_consu = self.env['product.product'].create({
            'name': 'Non-Service Product',
            'type': 'consu',
            'purchase_method': 'purchase',
        })
        wizard_invalid_type = self.env[
            'purchase.order.advance.payment'
        ].with_context(**ctx).create({
            'advance_payment_method': 'fixed',
            'fixed_amount': 50.0,
            'product_id': product_consu.id,
        })
        with self.assertRaises(UserError):
            wizard_invalid_type.action_create_advance_bill()

    def test_res_config_settings_field(self):
        """Verify reading and writing deposit product in config settings."""
        settings = self.env['res.config.settings'].create({
            'po_deposit_default_product_id': self.deposit_product.id,
        })
        settings.execute()
        param = self.env['ir.config_parameter'].sudo().get_int(
            'purchase_down_payment.po_deposit_default_product_id'
        )
        self.assertEqual(param, self.deposit_product.id)

    def test_grouped_purchase_orders_deduction(self):
        """Verify grouping and re-sequencing for multiple purchase orders."""
        po_a = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 2.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        po_a.button_confirm()

        po_b = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 3.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        po_b.button_confirm()

        # Create down payments on both
        for order in (po_a | po_b):
            wiz = self.env['purchase.order.advance.payment'].with_context(
                active_model='purchase.order',
                active_id=order.id,
                active_ids=order.ids,
            ).create({
                'advance_payment_method': 'fixed',
                'fixed_amount': 50.0,
                'product_id': self.deposit_product.id,
            })
            wiz.action_create_advance_bill()

        # Deduct together
        grouped_moves = (po_a | po_b)._deduct_payment(grouped=False, final=True)
        self.assertEqual(len(grouped_moves), 1)

    def test_order_with_sections_and_notes(self):
        """Verify down payment and deduction with section and note lines."""
        po_sec = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Section Header',
                    'product_qty': 0.0,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 4.0,
                    'price_unit': 50.0,
                }),
                (0, 0, {
                    'display_type': 'line_note',
                    'name': 'Note for vendor',
                    'product_qty': 0.0,
                }),
            ],
        })
        po_sec.button_confirm()

        ctx = {
            'active_model': 'purchase.order',
            'active_id': po_sec.id,
            'active_ids': po_sec.ids,
        }
        wiz = self.env['purchase.order.advance.payment'].with_context(
            **ctx
        ).create({
            'advance_payment_method': 'fixed',
            'fixed_amount': 50.0,
            'product_id': self.deposit_product.id,
        })
        wiz.action_create_advance_bill()

        wiz_deduct = self.env['purchase.order.advance.payment'].with_context(
            **ctx
        ).create({
            'advance_payment_method': 'delivered',
            'deduct_down_payments': True,
        })
        wiz_deduct.action_create_advance_bill()
        self.assertEqual(len(po_sec.invoice_ids), 2)

    def test_wizard_auto_create_deposit_product_and_open_invoices(self):
        """Verify automatic product creation when product_id is not set."""
        self.env['ir.config_parameter'].sudo().set_int(
            'purchase_down_payment.po_deposit_default_product_id',
            0,
        )
        po_new = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 1.0,
                    'price_unit': 300.0,
                }),
            ],
        })
        po_new.button_confirm()

        ctx = {
            'active_model': 'purchase.order',
            'active_id': po_new.id,
            'active_ids': po_new.ids,
            'open_invoices': True,
        }
        wizard = self.env['purchase.order.advance.payment'].with_context(
            **ctx
        ).create({
            'advance_payment_method': 'fixed',
            'fixed_amount': 100.0,
            'product_id': False,
        })
        action = wizard.action_create_advance_bill()
        self.assertEqual(action.get('res_model'), 'account.move')

        # Test regular bill without down payment deduction
        wizard_regular = self.env[
            'purchase.order.advance.payment'
        ].with_context(**ctx).create({
            'advance_payment_method': 'delivered',
            'deduct_down_payments': False,
        })
        action_regular = wizard_regular.action_create_advance_bill()
        self.assertEqual(action_regular.get('res_model'), 'account.move')

    def test_nothing_to_invoice_validation(self):
        """Verify error raised when order has nothing to invoice."""
        empty_po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [],
        })
        with self.assertRaises(UserError):
            empty_po._deduct_payment(final=False)

    def test_deduct_payment_with_date_and_zero_qty(self):
        """Verify _deduct_payment with date and zero qty on ordered line."""
        product_received = self.env['product.product'].create({
            'name': 'Test Received Product',
            'type': 'consu',
            'purchase_method': 'receive',
            'supplier_taxes_id': False,
        })
        po_zero = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_received.id,
                    'product_qty': 5.0,
                    'price_unit': 100.0,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 2.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        po_zero.button_confirm()
        test_date = fields.Date.today()
        moves = po_zero._deduct_payment(final=False, date=test_date)
        self.assertTrue(moves)
        self.assertEqual(moves[0].invoice_date, test_date)

    def test_access_rights(self):
        """Verify access rights for purchase.order, purchase.order.line,
        and advance payment wizard.
        """
        group_purchase_user = self.env.ref('purchase.group_purchase_user')
        models_to_check = [
            'purchase.order',
            'purchase.order.line',
            'purchase.order.advance.payment',
        ]
        for model_name in models_to_check:
            access = self.env['ir.access'].search([
                ('model_id.model', '=', model_name),
                ('group_id', '=', group_purchase_user.id),
            ])
            self.assertTrue(
                access,
                f"Access rule for {model_name} and purchase user must exist.",
            )

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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import timedelta
from unittest.mock import patch, PropertyMock
from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestMobileCreateInvoice(TransactionCase):
    """Test suite for mobile.invoice.wizard (mobile_create_invoice.py)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Invoice Wizard Customer',
            'email': 'wizard_cust@example.com',
        })
        cls.brand = cls.env['mobile.brand'].create({'brand_name': 'Xiaomi'})
        cls.model = cls.env['brand.model'].create({
            'mobile_brand_name': cls.brand.id,
            'mobile_brand_models': 'Redmi Note 13',
        })

        cls.part_screen = cls.env['product.product'].create({
            'name': 'Redmi Screen Assembly',
            'is_storable': True,
            'is_a_parts': True,
            'list_price': 80.0,
        })
        cls.part_cable = cls.env['product.product'].create({
            'name': 'Flex Cable',
            'is_storable': True,
            'is_a_parts': True,
            'list_price': 15.0,
        })

    def test_01_wizard_missing_service_record(self):
        """Verify wizard raises UserError when active_id is missing or invalid."""
        wizard = self.env['mobile.invoice.wizard'].with_context(
            active_id=False,
            active_model='mobile.service',
        ).create({
            'advance_payment_method': 'advance',
            'amount': 25.0,
        })
        with self.assertRaises(UserError):
            wizard.action_invoice_create()

    def test_02_wizard_missing_customer(self):
        """Verify wizard raises UserError when the service has no customer assigned."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })

        wizard = self.env['mobile.invoice.wizard'].with_context(
            active_id=service.id,
            active_model='mobile.service',
        ).create({
            'advance_payment_method': 'advance',
            'amount': 20.0,
        })
        with patch.object(
            type(service), 'person_name',
            new_callable=PropertyMock,
            return_value=self.env['res.partner']
        ):
            with self.assertRaises(UserError):
                wizard.action_invoice_create()

    def test_03_wizard_advance_invoice(self):
        """Verify wizard creates an advance payment invoice correctly."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })

        wizard = self.env['mobile.invoice.wizard'].with_context(
            active_id=service.id,
            active_model='mobile.service',
        ).create({
            'advance_payment_method': 'advance',
            'amount': 30.0,
        })
        action = wizard.action_invoice_create()
        self.assertTrue(action)
        self.assertTrue(service.first_payment_inv)
        self.assertTrue(service.first_invoice_created)

        inv = service.first_payment_inv
        self.assertEqual(inv.move_type, 'out_invoice')
        self.assertEqual(inv.partner_id.id, self.customer.id)
        self.assertEqual(inv.amount_untaxed, 30.0)
        self.assertEqual(len(inv.invoice_line_ids), 1)
        self.assertEqual(inv.invoice_line_ids[0].name, 'Mobile Service Advance')

    def test_04_wizard_full_amount_invoice_no_double_counting(self):
        """Verify full amount invoice applies unit price and quantity without double counting."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })

        # Add parts
        self.env['product.order.line'].create({
            'product_order_id': service.id,
            'product_id': self.part_screen.id,
            'product_uom': 'Units',
            'price_unit': 80.0,
            'product_uom_qty': 1.0,
        })
        self.env['product.order.line'].create({
            'product_order_id': service.id,
            'product_id': self.part_cable.id,
            'product_uom': 'Units',
            'price_unit': 15.0,
            'product_uom_qty': 2.0,
        })

        wizard = self.env['mobile.invoice.wizard'].with_context(
            active_id=service.id,
            active_model='mobile.service',
        ).create({
            'advance_payment_method': 'full_amount',
            'amount': 40.0,
        })
        action = wizard.action_invoice_create()
        self.assertTrue(action)
        self.assertTrue(service.first_payment_inv)

        inv = service.first_payment_inv
        # Expected calculation:
        # Service charge: 40.0
        # Screen: 80.0 * 1 = 80.0
        # Cable: 15.0 * 2 = 30.0
        # Untaxed Total: 40 + 80 + 30 = 150.0 (prevents double counting)
        self.assertEqual(inv.amount_untaxed, 150.0)

        screen_line = inv.invoice_line_ids.filtered(lambda l: l.product_id == self.part_screen)
        self.assertEqual(len(screen_line), 1)
        self.assertEqual(screen_line.price_unit, 80.0)
        self.assertEqual(screen_line.quantity, 1.0)
        self.assertEqual(screen_line.price_subtotal, 80.0)

        cable_line = inv.invoice_line_ids.filtered(lambda l: l.product_id == self.part_cable)
        self.assertEqual(len(cable_line), 1)
        self.assertEqual(cable_line.price_unit, 15.0)
        self.assertEqual(cable_line.quantity, 2.0)
        self.assertEqual(cable_line.price_subtotal, 30.0)

        service_line = inv.invoice_line_ids.filtered(lambda l: l.name == 'Mobile Service Charge')
        self.assertEqual(len(service_line), 1)
        self.assertEqual(service_line.price_unit, 40.0)
        self.assertEqual(service_line.quantity, 1.0)
        self.assertEqual(service_line.price_subtotal, 40.0)

    def test_05_wizard_nothing_to_invoice(self):
        """Verify wizard raises UserError when there is no amount and no parts to invoice."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })

        wizard = self.env['mobile.invoice.wizard'].with_context(
            active_id=service.id,
            active_model='mobile.service',
        ).create({
            'advance_payment_method': 'full_amount',
            'amount': 0.0,
        })
        with self.assertRaises(UserError):
            wizard.action_invoice_create()

    def test_06_wizard_invoiced_qty_exceeds_used(self):
        """Verify wizard raises UserError if used qty is less than invoiced qty."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })
        line = self.env['product.order.line'].create({
            'product_order_id': service.id,
            'product_id': self.part_screen.id,
            'product_uom': 'Units',
            'price_unit': 80.0,
            'product_uom_qty': 1.0,
        })
        # Simulate invalid state where invoiced qty > used qty
        line.qty_invoiced = 2.0

        wizard = self.env['mobile.invoice.wizard'].with_context(
            active_id=service.id,
            active_model='mobile.service',
        ).create({
            'advance_payment_method': 'full_amount',
            'amount': 20.0,
        })
        with self.assertRaises(UserError):
            wizard.action_invoice_create()

    def test_07_wizard_action_return_format(self):
        """Verify wizard returns proper act_window action pointing to the invoice."""
        service = self.env['mobile.service'].create({
            'person_name': self.customer.id,
            'brand_name': self.brand.id,
            'model_name': self.model.id,
            'return_date': fields.Date.today() + timedelta(days=2),
        })
        wizard = self.env['mobile.invoice.wizard'].with_context(
            active_id=service.id,
            active_model='mobile.service',
        ).create({
            'advance_payment_method': 'advance',
            'amount': 50.0,
        })
        action = wizard.action_invoice_create()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'account.move')
        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('res_id'), service.first_payment_inv.id)

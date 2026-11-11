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
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.website_customer_note.controllers.website_customer_note import (
    WebsiteSaleCustomerNote,
)
from odoo.addons.website_sale.tests.common import MockRequest


@tagged('post_install', '-at_install')
class TestWebsiteCustomerNote(TransactionCase):
    """Unit test suite for Website Customer Note module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Customer Note Test Partner',
            'email': 'customer.note.test@example.com',
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.controller = WebsiteSaleCustomerNote()

    def test_01_customer_note_default_value(self):
        """Test default value of customer_note on newly created sale order."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertFalse(order.customer_note)

    def test_02_create_sale_order_with_customer_note(self):
        """Test creating a sale order with customer_note specified."""
        note_text = "Please leave the package at the front porch."
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'customer_note': note_text,
        })
        self.assertEqual(order.customer_note, note_text)

    def test_03_write_customer_note_orm(self):
        """Test updating customer_note via standard ORM write."""
        note_text = "Ring the doorbell upon arrival."
        self.sale_order.write({'customer_note': note_text})
        self.assertEqual(self.sale_order.customer_note, note_text)

    def test_04_write_customer_note_empty_and_special_chars(self):
        """Test customer_note with empty string and multi-line unicode text."""
        # Empty string
        self.sale_order.write({'customer_note': ''})
        self.assertEqual(self.sale_order.customer_note, '')

        # Multiline and special unicode characters
        multiline_note = "Line 1: Urgent delivery\nLine 2: Gate code #1234\nLine 3: 📦"
        self.sale_order.write({'customer_note': multiline_note})
        self.assertEqual(self.sale_order.customer_note, multiline_note)

    def test_05_multi_recordset_customer_note(self):
        """Test customer_note handling across multiple sale order records."""
        orders = self.env['sale.order'].create([
            {
                'partner_id': self.partner.id,
                'customer_note': 'Initial Note A',
            },
            {
                'partner_id': self.partner.id,
                'customer_note': 'Initial Note B',
            },
        ])
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0].customer_note, 'Initial Note A')
        self.assertEqual(orders[1].customer_note, 'Initial Note B')

        # Update note across multiple records simultaneously
        orders.write({'customer_note': 'Bulk Updated Note'})
        self.assertTrue(
            all(note == 'Bulk Updated Note' for note in orders.mapped('customer_note')),
        )

    def test_06_controller_save_customer_note_success(self):
        """Test saving customer note through the controller endpoint."""
        note_text = "Controller delivery note"
        with MockRequest(self.env) as req:
            req.cart = self.sale_order
            response = self.controller.save_customer_note(
                customer_note=note_text,
                order_id=self.sale_order.id,
            )
        self.assertTrue(response.get('success'))
        self.assertEqual(self.sale_order.customer_note, note_text)

    def test_07_controller_save_customer_note_no_active_cart(self):
        """Test controller response when no active cart exists in session."""
        with MockRequest(self.env) as req:
            req.cart = None
            response = self.controller.save_customer_note(
                customer_note="Note without cart",
                order_id=self.sale_order.id,
            )
        self.assertFalse(response.get('success'))
        self.assertEqual(response.get('error'), 'No active order found')

    def test_08_controller_save_customer_note_access_denied(self):
        """Test controller denies modifying an order other than the session cart."""
        other_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        with MockRequest(self.env) as req:
            req.cart = self.sale_order
            response = self.controller.save_customer_note(
                customer_note="Tampered note",
                order_id=other_order.id,
            )
        self.assertFalse(response.get('success'))
        self.assertEqual(response.get('error'), 'Access denied')
        self.assertFalse(other_order.customer_note)

    def test_09_controller_save_customer_note_invalid_order_id(self):
        """Test controller response when order_id has invalid non-numeric format."""
        with MockRequest(self.env) as req:
            req.cart = self.sale_order
            response = self.controller.save_customer_note(
                customer_note="Note for invalid ID",
                order_id="not_an_integer",
            )
        self.assertFalse(response.get('success'))
        self.assertEqual(response.get('error'), 'Invalid order ID')

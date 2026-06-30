# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPantryOrder(common.TransactionCase):
    """Test cases for pantry.order and pantry.order.line models."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for pantry order tests."""
        super().setUpClass()
        # Create a pantry product
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Coffee',
            'list_price': 50.0,
            'pantry_product': True,
            'type': 'consu',
        })
        cls.product = cls.product_template.product_variant_id
        cls.product_2_template = cls.env['product.template'].create({
            'name': 'Test Snack',
            'list_price': 30.0,
            'pantry_product': True,
            'type': 'consu',
        })
        cls.product_2 = cls.product_2_template.product_variant_id
        cls.partner = cls.env.user.partner_id

    def test_01_pantry_order_creation_with_sequence(self):
        """Test that pantry order gets a sequence number on creation."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertTrue(order.name, "Order should have a name assigned.")
        self.assertNotEqual(order.name, 'New',
                            "Order name should not remain 'New'.")
        self.assertTrue(order.name.startswith('PAO/'),
                        "Order name should start with 'PAO/' prefix.")

    def test_02_pantry_order_default_state(self):
        """Test that a new pantry order defaults to 'draft' state."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(order.state, 'draft',
                         "New order should be in 'draft' state.")

    def test_03_pantry_order_default_partner(self):
        """Test that the partner defaults to the current user's partner."""
        order = self.env['pantry.order'].create({})
        self.assertEqual(order.partner_id, self.env.user.partner_id,
                         "Default partner should be the current user's partner.")

    def test_04_pantry_order_default_date(self):
        """Test that the order date is automatically set."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertTrue(order.date_order,
                        "Order date should be automatically set.")

    def test_05_action_confirm_pantry_order(self):
        """Test confirming a pantry order changes state to 'confirmed'."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(order.state, 'draft')
        order.action_confirm_pantry_order()
        self.assertEqual(order.state, 'confirmed',
                         "Order state should be 'confirmed' after confirmation.")

    def test_06_amount_total_computation(self):
        """Test that amount_total is correctly computed from order lines."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
            'order_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 2,
                    'unit_price': 50.0,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'quantity': 3,
                    'unit_price': 30.0,
                }),
            ],
        })
        # Line 1: 2 * 50 = 100, Line 2: 3 * 30 = 90 => Total = 190
        self.assertEqual(order.amount_total, 190.0,
                         "Total amount should be 190.0.")

    def test_07_amount_total_empty_order(self):
        """Test that amount_total is 0 for an order with no lines."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(order.amount_total, 0.0,
                         "Total amount should be 0.0 for empty order.")

    def test_08_order_line_subtotal_computation(self):
        """Test that order line subtotal is correctly computed."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['pantry.order.line'].create({
            'pantry_order_id': order.id,
            'product_id': self.product.id,
            'quantity': 5,
            'unit_price': 50.0,
        })
        self.assertEqual(line.subtotal, 250.0,
                         "Subtotal should be quantity * unit_price = 250.0.")

    def test_09_order_line_subtotal_zero_quantity(self):
        """Test subtotal with zero quantity."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        line = self.env['pantry.order.line'].create({
            'pantry_order_id': order.id,
            'product_id': self.product.id,
            'quantity': 0,
            'unit_price': 50.0,
        })
        self.assertEqual(line.subtotal, 0.0,
                         "Subtotal should be 0.0 when quantity is 0.")

    def test_10_order_line_updates_total(self):
        """Test that adding order lines updates the order's total."""
        order = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(order.amount_total, 0.0)
        self.env['pantry.order.line'].create({
            'pantry_order_id': order.id,
            'product_id': self.product.id,
            'quantity': 2,
            'unit_price': 50.0,
        })
        self.assertEqual(order.amount_total, 100.0,
                         "Total should update to 100.0 after adding a line.")

    def test_11_multiple_sequence_numbers(self):
        """Test that multiple orders get unique sequence numbers."""
        order_1 = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        order_2 = self.env['pantry.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertNotEqual(order_1.name, order_2.name,
                            "Each order should have a unique sequence number.")

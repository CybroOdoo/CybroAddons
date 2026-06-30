# -*- coding: utf-8 -*-
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestProductProduct(common.TransactionCase):
    """Test cases for product.product pantry extensions."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for product tests."""
        super().setUpClass()
        cls.product_template = cls.env['product.template'].create({
            'name': 'Pantry Tea',
            'list_price': 25.0,
            'pantry_product': True,
            'type': 'consu',
        })
        cls.product = cls.product_template.product_variant_id
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Pantry Juice',
            'list_price': 40.0,
            'pantry_product': True,
            'type': 'consu',
        })
        cls.product_2 = cls.product_template_2.product_variant_id
        cls.partner = cls.env.user.partner_id

    def test_01_pantry_product_boolean(self):
        """Test that pantry_product field is correctly set on template."""
        self.assertTrue(self.product_template.pantry_product,
                        "Product template should be marked as pantry product.")

    def test_02_pantry_product_boolean_false(self):
        """Test creating a non-pantry product."""
        template = self.env['product.template'].create({
            'name': 'Regular Product',
            'list_price': 100.0,
            'pantry_product': False,
        })
        self.assertFalse(template.pantry_product,
                         "Product template should not be a pantry product.")

    def test_03_default_quantity(self):
        """Test that product default quantity is 1."""
        self.assertEqual(self.product.quantity, 1,
                         "Default product quantity should be 1.")

    def test_04_quantity_increment(self):
        """Test incrementing product quantity."""
        self.product.action_quantity_increment()
        self.assertEqual(self.product.quantity, 2,
                         "Quantity should be 2 after one increment.")
        self.product.action_quantity_increment()
        self.assertEqual(self.product.quantity, 3,
                         "Quantity should be 3 after two increments.")

    def test_05_quantity_decrement(self):
        """Test decrementing product quantity."""
        self.product.quantity = 3
        self.product.action_quantity_decrement()
        self.assertEqual(self.product.quantity, 2,
                         "Quantity should be 2 after decrement from 3.")

    def test_06_quantity_decrement_minimum(self):
        """Test that quantity cannot go below 1."""
        self.assertEqual(self.product.quantity, 1)
        self.product.action_quantity_decrement()
        self.assertEqual(self.product.quantity, 1,
                         "Quantity should remain 1; cannot go below 1.")

    def test_07_action_buy_pantry_creates_new_order(self):
        """Test that action_buy_pantry creates a new pantry order."""
        # Ensure no existing draft orders
        existing = self.env['pantry.order'].search([
            ('partner_id', '=', self.partner.id),
            ('state', '=', 'draft'),
        ])
        existing.unlink()
        self.product.quantity = 2
        result = self.product.action_buy_pantry()
        self.assertEqual(result['res_model'], 'pantry.order')
        order = self.env['pantry.order'].browse(result['res_id'])
        self.assertEqual(order.partner_id, self.partner)
        self.assertEqual(len(order.order_line_ids), 1)
        self.assertEqual(order.order_line_ids.product_id, self.product)
        self.assertEqual(order.order_line_ids.quantity, 2)
        self.assertEqual(order.order_line_ids.unit_price, 25.0)
        # Quantity should reset to 1 after buying
        self.assertEqual(self.product.quantity, 1,
                         "Product quantity should reset to 1 after buy.")

    def test_08_action_buy_pantry_adds_to_existing_order(self):
        """Test that buying a new product adds a line to existing draft order."""
        existing = self.env['pantry.order'].search([
            ('partner_id', '=', self.partner.id),
            ('state', '=', 'draft'),
        ])
        existing.unlink()
        # First purchase creates order
        self.product.quantity = 1
        result = self.product.action_buy_pantry()
        order = self.env['pantry.order'].browse(result['res_id'])
        self.assertEqual(len(order.order_line_ids), 1)
        # Second purchase with different product adds line to same order
        self.product_2.quantity = 3
        result_2 = self.product_2.action_buy_pantry()
        order_2 = self.env['pantry.order'].browse(result_2['res_id'])
        self.assertEqual(order.id, order_2.id,
                         "Should reuse existing draft order.")
        self.assertEqual(len(order.order_line_ids), 2,
                         "Order should now have 2 lines.")

    def test_09_action_buy_pantry_increments_existing_product(self):
        """Test that buying same product again increments quantity on existing line."""
        existing = self.env['pantry.order'].search([
            ('partner_id', '=', self.partner.id),
            ('state', '=', 'draft'),
        ])
        existing.unlink()
        # First purchase
        self.product.quantity = 2
        result = self.product.action_buy_pantry()
        order = self.env['pantry.order'].browse(result['res_id'])
        self.assertEqual(order.order_line_ids.quantity, 2)
        # Buy same product again
        self.product.quantity = 3
        self.product.action_buy_pantry()
        self.assertEqual(len(order.order_line_ids), 1,
                         "Should still have 1 line for the same product.")
        self.assertEqual(order.order_line_ids.quantity, 5,
                         "Quantity should be 2 + 3 = 5.")

    def test_10_action_buy_pantry_returns_action(self):
        """Test that action_buy_pantry returns a valid window action."""
        result = self.product.action_buy_pantry()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'pantry.order')
        self.assertEqual(result['view_mode'], 'form')
        self.assertEqual(result['target'], 'current')
        self.assertIn('res_id', result)

    def test_11_action_buy_does_not_add_to_confirmed_order(self):
        """Test that buying creates new order if existing order is confirmed."""
        existing = self.env['pantry.order'].search([
            ('partner_id', '=', self.partner.id),
            ('state', '=', 'draft'),
        ])
        existing.unlink()
        # Create and confirm an order
        self.product.quantity = 1
        result = self.product.action_buy_pantry()
        order = self.env['pantry.order'].browse(result['res_id'])
        order.action_confirm_pantry_order()
        self.assertEqual(order.state, 'confirmed')
        # New purchase should create a new draft order
        self.product.quantity = 1
        result_2 = self.product.action_buy_pantry()
        new_order = self.env['pantry.order'].browse(result_2['res_id'])
        self.assertNotEqual(order.id, new_order.id,
                            "Should create a new order since previous is confirmed.")
        self.assertEqual(new_order.state, 'draft')

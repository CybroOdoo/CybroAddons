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
"""Test suite for Previous Sale/Purchase Product Rates module."""
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSalePurchasePreviousProductCost(TransactionCase):
    """Unit tests for Previous Sale and Purchase Product Rates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.customer_2 = cls.env['res.partner'].create({
            'name': 'Second Test Customer',
        })
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor',
        })
        cls.vendor_2 = cls.env['res.partner'].create({
            'name': 'Second Test Vendor',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Rate Product',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 60.0,
        })
        cls.unused_product = cls.env['product.product'].create({
            'name': 'Unused Rate Product',
            'type': 'consu',
        })

        # Sale orders
        cls.sale_order_1 = cls.env['sale.order'].create({
            'partner_id': cls.customer.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 95.0,
            })],
        })
        cls.sale_line_1 = cls.sale_order_1.order_line[0]

        cls.sale_order_2 = cls.env['sale.order'].create({
            'partner_id': cls.customer_2.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 5.0,
                'price_unit': 90.0,
            })],
        })
        cls.sale_line_2 = cls.sale_order_2.order_line[0]

        # Purchase orders
        cls.purchase_order_1 = cls.env['purchase.order'].create({
            'partner_id': cls.vendor.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_qty': 10.0,
                'price_unit': 55.0,
            })],
        })
        cls.purchase_line_1 = cls.purchase_order_1.order_line[0]

        cls.purchase_order_2 = cls.env['purchase.order'].create({
            'partner_id': cls.vendor_2.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_qty': 20.0,
                'price_unit': 50.0,
            })],
        })
        cls.purchase_line_2 = cls.purchase_order_2.order_line[0]

    def test_order_partner_id_field_properties(self):
        """Test that order_partner_id is non-stored on product.product."""
        field = self.env['product.product']._fields['order_partner_id']
        self.assertFalse(field.store, "order_partner_id should not be stored in database")
        self.assertTrue(field.compute, "order_partner_id should be computed from context")

    def test_order_partner_id_context_dynamism_no_stale_cache(self):
        """Test that order_partner_id dynamically reflects context without stale cache."""
        # 1. Product with Customer 1
        p1 = self.product.with_context(default_order_partner_id=self.customer.id)
        self.assertEqual(p1.order_partner_id, self.customer)

        # 2. Same product with Customer 2 - must immediately reflect Customer 2 without stale data
        p2 = self.product.with_context(default_order_partner_id=self.customer_2.id)
        self.assertEqual(p2.order_partner_id, self.customer_2)

        # 3. Same product with no context - must be False, not stale from previous calls
        p3 = self.product.with_context(default_order_partner_id=False)
        self.assertFalse(p3.order_partner_id)

    def test_product_standard_write(self):
        """Verify normal product write continues to work via standard super()."""
        self.product.write({'list_price': 120.0})
        self.assertEqual(self.product.list_price, 120.0)

    def test_sale_order_line_action_get_product_form(self):
        """Test opening product form from sale order line with partner prefilled in context."""
        action = self.sale_line_1.action_get_product_form()
        self.assertEqual(action.get('res_model'), 'product.product')
        self.assertEqual(action.get('res_id'), self.product.id)
        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('target'), 'current')
        self.assertIn('default_order_partner_id', action.get('context', {}))
        self.assertEqual(
            action['context']['default_order_partner_id'],
            self.customer.id,
            "Customer partner should be prefilled in context from sale order line",
        )

    def test_sale_order_line_action_without_product(self):
        """Test action when line has no product."""
        empty_line = self.env['sale.order.line'].new({'order_id': self.sale_order_1.id})
        action = empty_line.action_get_product_form()
        self.assertEqual(action.get('type'), 'ir.actions.act_window_close')

    def test_purchase_order_line_action_get_product_form(self):
        """Test opening product form from purchase order line with partner prefilled in context."""
        action = self.purchase_line_1.action_get_product_form()
        self.assertEqual(action.get('res_model'), 'product.product')
        self.assertEqual(action.get('res_id'), self.product.id)
        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('target'), 'current')
        self.assertIn('default_order_partner_id', action.get('context', {}))
        self.assertEqual(
            action['context']['default_order_partner_id'],
            self.vendor.id,
            "Vendor partner should be prefilled in context from purchase order line",
        )

    def test_purchase_order_line_action_without_product(self):
        """Test action when line has no product."""
        empty_line = self.env['purchase.order.line'].new({'order_id': self.purchase_order_1.id})
        action = empty_line.action_get_product_form()
        self.assertEqual(action.get('type'), 'ir.actions.act_window_close')

    def test_action_sale_product_prices_filtered_by_partner(self):
        """Test viewing previous sale rates filtered by order_partner_id."""
        product_with_context = self.product.with_context(
            default_order_partner_id=self.customer.id
        )
        action = product_with_context.action_sale_product_prices()
        self.assertEqual(action.get('res_model'), 'sale.order.line')
        self.assertEqual(action.get('view_mode'), 'list')
        self.assertEqual(
            action.get('context', {}).get('default_order_partner_id'),
            self.customer.id,
            "History action must pass default_order_partner_id through context",
        )

        # Check domain returned
        domain = action.get('domain', [])
        sale_lines = self.env['sale.order.line'].search(domain)
        self.assertIn(self.sale_line_1, sale_lines)
        self.assertNotIn(self.sale_line_2, sale_lines)

    def test_action_sale_product_prices_all_partners(self):
        """Test viewing previous sale rates when no partner is specified."""
        product = self.product.with_context(default_order_partner_id=False)
        action = product.action_sale_product_prices()
        self.assertEqual(action.get('res_model'), 'sale.order.line')

        domain = action.get('domain', [])
        sale_lines = self.env['sale.order.line'].search(domain)
        self.assertIn(self.sale_line_1, sale_lines)
        self.assertIn(self.sale_line_2, sale_lines)

    def test_action_sale_product_prices_no_history(self):
        """Test UserError raised when product has no sales history."""
        with self.assertRaises(UserError):
            self.unused_product.action_sale_product_prices()

    def test_action_purchase_product_prices_filtered_by_partner(self):
        """Test viewing previous purchase rates filtered by order_partner_id."""
        product_with_context = self.product.with_context(
            default_order_partner_id=self.vendor.id
        )
        action = product_with_context.action_purchase_product_prices()
        self.assertEqual(action.get('res_model'), 'purchase.order.line')
        self.assertEqual(action.get('view_mode'), 'list')
        self.assertEqual(
            action.get('context', {}).get('default_order_partner_id'),
            self.vendor.id,
            "History action must pass default_order_partner_id through context",
        )

        domain = action.get('domain', [])
        purchase_lines = self.env['purchase.order.line'].search(domain)
        self.assertIn(self.purchase_line_1, purchase_lines)
        self.assertNotIn(self.purchase_line_2, purchase_lines)

    def test_action_purchase_product_prices_all_partners(self):
        """Test viewing previous purchase rates when no partner is specified."""
        product = self.product.with_context(default_order_partner_id=False)
        action = product.action_purchase_product_prices()
        self.assertEqual(action.get('res_model'), 'purchase.order.line')

        domain = action.get('domain', [])
        purchase_lines = self.env['purchase.order.line'].search(domain)
        self.assertIn(self.purchase_line_1, purchase_lines)
        self.assertIn(self.purchase_line_2, purchase_lines)

    def test_action_purchase_product_prices_no_history(self):
        """Test UserError raised when product has no purchase history."""
        with self.assertRaises(UserError):
            self.unused_product.action_purchase_product_prices()

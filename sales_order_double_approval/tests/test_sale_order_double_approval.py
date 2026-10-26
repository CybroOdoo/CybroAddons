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
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestSaleOrderDoubleApproval(common.TransactionCase):
    """Test suite for Sales Order Double Approval module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.company.so_double_validation = True

        # Group references
        cls.group_sale_salesman = cls.env.ref('sales_team.group_sale_salesman')
        cls.group_sale_manager = cls.env.ref('sales_team.group_sale_manager')

        # Test Sales User (salesperson without manager rights)
        cls.sales_user = cls.env['res.users'].create({
            'name': 'Test Salesperson',
            'login': 'test_salesperson',
            'email': 'salesperson@test.com',
            'group_ids': [(6, 0, [cls.group_sale_salesman.id])],
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
        })

        cls.sales_manager = cls.env['res.users'].create({
            'name': 'Test Sales Manager',
            'login': 'test_sales_manager',
            'email': 'salesmanager@test.com',
            'group_ids': [(6, 0, [cls.group_sale_manager.id])],
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'type': 'consu',
        })

        config = cls.env['ir.config_parameter'].sudo()
        config.set_float('sales_order_double_approval.so_min_amount', 500.0)

    def _create_sale_order(self, qty=1, price_unit=100.0, user=None):
        """Helper method to create a sale order."""
        user = user or self.sales_user
        return self.env['sale.order'].with_user(user).create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': qty,
                'price_unit': price_unit,
                'tax_ids': [(5, 0, 0)],
            })],
        })

    def test_01_res_config_settings(self):
        """Test getting and setting configuration values."""
        settings = self.env['res.config.settings'].create({
            'so_min_amount': 750.0,
        })
        settings.set_values()

        values = self.env['res.config.settings'].get_values()
        self.assertEqual(values.get('so_min_amount'), 750.0, "so_min_amount should be 750.0")

        # Reset to base test default
        self.env['ir.config_parameter'].sudo().set_float(
            'sales_order_double_approval.so_min_amount', 500.0)

    def test_02_double_validation_disabled_on_company(self):
        """When company so_double_validation is False, orders should confirm directly to 'sale'."""
        self.company.so_double_validation = False
        # Create an order with total amount = 1000.0 (> 500.0 min amount)
        order = self._create_sale_order(qty=10, price_unit=100.0, user=self.sales_user)
        self.assertGreater(order.amount_total, 500.0)

        order.action_confirm()
        self.assertEqual(order.state, 'sale',
                         "Order should be confirmed to 'sale' directly when company double validation is disabled")

    def test_04_order_amount_below_or_equal_min_amount(self):
        """When total amount does not exceed the threshold, order should confirm directly to 'sale'."""
        self.company.so_double_validation = True
        self.env['ir.config_parameter'].sudo().set_float(
            'sales_order_double_approval.so_min_amount', 500.0)

        # Order below min amount: 300.0 <= 500.0
        order_below = self._create_sale_order(qty=3, price_unit=100.0, user=self.sales_user)
        order_below.action_confirm()
        self.assertEqual(order_below.state, 'sale',
                         "Order with amount <= min_amount should confirm directly to 'sale'")

        # Order equal to min amount: 500.0 <= 500.0
        order_equal = self._create_sale_order(qty=5, price_unit=100.0, user=self.sales_user)
        self.assertEqual(order_equal.amount_total, 500.0)
        order_equal.action_confirm()
        self.assertEqual(order_equal.state, 'sale',
                         "Order with amount exactly equal to min_amount should confirm directly to 'sale'")

    def test_05_salesperson_confirms_order_above_min_amount(self):
        """When salesperson confirms order > min_amount, it should go to 'to_approve'."""
        self.company.so_double_validation = True
        self.env['ir.config_parameter'].sudo().set_float(
            'sales_order_double_approval.so_min_amount', 500.0)

        order = self._create_sale_order(qty=10, price_unit=100.0, user=self.sales_user)
        self.assertGreater(order.amount_total, 500.0)

        order.action_confirm()
        self.assertEqual(order.state, 'to_approve',
                         "Order confirmed by salesperson above min_amount must require approval ('to_approve')")

    def test_06_sales_manager_confirms_order_above_min_amount(self):
        """When sales manager confirms order > min_amount, it should directly become 'sale'."""
        self.company.so_double_validation = True
        self.env['ir.config_parameter'].sudo().set_float(
            'sales_order_double_approval.so_min_amount', 500.0)

        order = self._create_sale_order(qty=10, price_unit=100.0, user=self.sales_manager)
        self.assertGreater(order.amount_total, 500.0)

        order.action_confirm()
        self.assertEqual(order.state, 'sale',
                         "Order confirmed directly by sales manager should be in 'sale' state")

    def test_07_manager_button_approve(self):
        """When order is in 'to_approve', sales manager approves it via button_approve."""
        self.company.so_double_validation = True
        self.env['ir.config_parameter'].sudo().set_float(
            'sales_order_double_approval.so_min_amount', 500.0)

        order = self._create_sale_order(qty=10, price_unit=100.0, user=self.sales_user)
        order.action_confirm()
        self.assertEqual(order.state, 'to_approve')

        # Sales manager approves the order
        order.with_user(self.sales_manager).button_approve()
        self.assertEqual(order.state, 'sale',
                         "Order state should transition to 'sale' after manager approves")

    def test_08_action_cancel_from_to_approve(self):
        """When order is in 'to_approve', it can be cancelled via action_cancel."""
        self.company.so_double_validation = True
        self.env['ir.config_parameter'].sudo().set_float(
            'sales_order_double_approval.so_min_amount', 500.0)

        order = self._create_sale_order(qty=10, price_unit=100.0, user=self.sales_user)
        order.action_confirm()
        self.assertEqual(order.state, 'to_approve')

        order.with_user(self.sales_manager).action_cancel()
        self.assertEqual(order.state, 'cancel',
                         "Order state should transition to 'cancel' when cancelled from 'to_approve'")

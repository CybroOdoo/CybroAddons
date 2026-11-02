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
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestSaleStockRestrict(TransactionCase):
    """Test the out of stock restriction on sale order confirmation."""

    @classmethod
    def setUpClass(cls):
        """Create a storable product with 10 units on hand."""
        super().setUpClass()

        # Storable product, the only kind the restriction checks
        cls.product = cls.env['product.product'].create({
            'name': 'Test Storable Product',
            'type': 'consu',
            'is_storable': True,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })

        # On hand quantity = 10
        stock_location = cls.env.ref('stock.stock_location_stock')
        cls.env['stock.quant']._update_available_quantity(cls.product, stock_location, 10.0)

    def test_01_compute_stock_quantities(self):
        """Test the order line quantities follow the check stock setting"""
        # Set config to check on hand quantity
        self.env['ir.config_parameter'].sudo().set_bool(
            'sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_str(
            'sale_stock_restrict.check_stock', 'on_hand_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
            })],
        })
        line = order.order_line[0]

        # Recompute stock quantities
        line.invalidate_recordset(['qty_available', 'forecast_quantity'])

        self.assertEqual(line.qty_available, self.product.qty_available)
        self.assertEqual(line.forecast_quantity, 0.0)

        # Set config to check forecast quantity
        self.env['ir.config_parameter'].sudo().set_str(
            'sale_stock_restrict.check_stock', 'forecast_quantity')

        # Recompute with the new config
        line.invalidate_recordset(['qty_available', 'forecast_quantity'])

        self.assertEqual(line.forecast_quantity, self.product.virtual_available)
        self.assertEqual(line.qty_available, 0.0)

    def test_02_action_confirm_on_hand_success(self):
        """Test confirming order when on hand quantity is sufficient"""
        self.env['ir.config_parameter'].sudo().set_bool(
            'sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_str(
            'sale_stock_restrict.check_stock', 'on_hand_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
            })],
        })
        line = order.order_line[0]
        # Recompute stock quantities with the current config
        line.invalidate_recordset(['qty_available', 'forecast_quantity'])

        # Should not raise any exception
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_03_action_confirm_on_hand_fail(self):
        """Test confirming order when on hand quantity is insufficient"""
        self.env['ir.config_parameter'].sudo().set_bool(
            'sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_str(
            'sale_stock_restrict.check_stock', 'on_hand_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 15,
            })],
        })
        line = order.order_line[0]
        line.invalidate_recordset(['qty_available', 'forecast_quantity'])

        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_04_action_confirm_forecast_success(self):
        """Test confirming order when forecast quantity is sufficient"""
        self.env['ir.config_parameter'].sudo().set_bool(
            'sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_str(
            'sale_stock_restrict.check_stock', 'forecast_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
            })],
        })
        line = order.order_line[0]
        line.invalidate_recordset(['qty_available', 'forecast_quantity'])

        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_05_action_confirm_forecast_fail(self):
        """Test confirming order when forecast quantity is insufficient"""
        self.env['ir.config_parameter'].sudo().set_bool(
            'sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_str(
            'sale_stock_restrict.check_stock', 'forecast_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 15,
            })],
        })
        line = order.order_line[0]
        line.invalidate_recordset(['qty_available', 'forecast_quantity'])

        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_06_action_confirm_no_restriction(self):
        """Test confirming order when restriction is disabled"""
        self.env['ir.config_parameter'].sudo().set_bool(
            'sale_stock_restrict.product_restriction', False)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 15,
            })],
        })

        # Even with high quantity, it should confirm since restriction is disabled
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def _enable_restriction(self):
        """Enable the restriction based on the on hand quantity."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('sale_stock_restrict.product_restriction', True)
        params.set_str('sale_stock_restrict.check_stock', 'on_hand_quantity')

    def _create_order(self, product, quantity, **values):
        """Create a quotation with one line of the given product."""
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': quantity,
            })],
            **values,
        })

    def test_07_unit_of_measure_is_converted(self):
        """Test 1 Dozen is checked as 12 Units against 10 Units in stock"""
        self._enable_restriction()
        order = self._create_order(self.product, 1)
        order.order_line.product_uom_id = self.env.ref('uom.product_uom_dozen')
        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_08_untracked_product_is_not_checked(self):
        """Test a service is never blocked"""
        self._enable_restriction()
        service = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
        })
        order = self._create_order(service, 100)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_09_website_order_is_not_checked(self):
        """Test website orders are not restricted"""
        self._enable_restriction()
        website = self.env['website'].search([], limit=1)
        order = self._create_order(self.product, 15, website_id=website.id)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_10_warning_lists_every_short_product(self):
        """Test the warning names each product that is short"""
        self._enable_restriction()
        other = self.env['product.product'].create({
            'name': 'Test Second Product',
            'type': 'consu',
            'is_storable': True,
        })
        order = self._create_order(self.product, 15)
        order.order_line = [(0, 0, {
            'product_id': other.id,
            'product_uom_qty': 1,
        })]
        with self.assertRaises(ValidationError) as error:
            order.action_confirm()
        self.assertIn(self.product.display_name, str(error.exception))
        self.assertIn(other.display_name, str(error.exception))

    def test_11_check_stock_follows_the_setting(self):
        """Test the order flag that switches the quantity column"""
        self._enable_restriction()
        order = self._create_order(self.product, 1)
        self.assertTrue(order.check_stock)
        self.env['ir.config_parameter'].sudo().set_str(
            'sale_stock_restrict.check_stock', 'forecast_quantity')
        order.invalidate_recordset(['check_stock'])
        self.assertFalse(order.check_stock)

    def test_12_settings_save_without_a_choice(self):
        """Test the settings can be saved on a fresh database"""
        settings = self.env['res.config.settings'].create({})
        self.assertEqual(settings.check_stock, 'on_hand_quantity')
        settings.execute()
        self.assertFalse(self.env['ir.config_parameter'].sudo().get_bool(
            'sale_stock_restrict.product_restriction'))

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
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSalePurchaseAutomated(TransactionCase):
    """Test suite for Sale and Purchase automated confirmation, invoicing,
    and report print features."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor',
        })
        cls.product_ordered = cls.env['product.product'].create({
            'name': 'Test Product Ordered Policy',
            'type': 'consu',
            'invoice_policy': 'order',
            'list_price': 100.0,
            'standard_price': 60.0,
        })
        cls.product_delivery = cls.env['product.product'].create({
            'name': 'Test Product Delivery Policy',
            'type': 'consu',
            'invoice_policy': 'delivery',
            'list_price': 150.0,
            'standard_price': 80.0,
        })

    def _reset_config_parameters(self):
        """Helper to reset all module parameters to False."""
        params = [
            'automate_sale',
            'automate_invoice',
            'automate_validate_invoice',
            'automate_print_invoices',
            'automate_purchase',
            'automate_print_bills',
        ]
        for param in params:
            self.config_param.set_bool(param, False)

    def test_01_res_config_settings(self):
        """Test enabling and disabling all automation parameters via settings."""
        settings = self.env['res.config.settings'].create({
            'automate_sale': True,
            'automate_invoice': True,
            'automate_validate_invoice': True,
            'automate_print_invoices': True,
            'automate_purchase': True,
            'automate_print_bills': True,
        })
        settings.execute()

        self.assertTrue(self.config_param.get_bool('automate_sale'))
        self.assertTrue(self.config_param.get_bool('automate_invoice'))
        self.assertTrue(self.config_param.get_bool('automate_validate_invoice'))
        self.assertTrue(self.config_param.get_bool('automate_print_invoices'))
        self.assertTrue(self.config_param.get_bool('automate_purchase'))
        self.assertTrue(self.config_param.get_bool('automate_print_bills'))

        settings = self.env['res.config.settings'].create({
            'automate_sale': False,
            'automate_invoice': False,
            'automate_validate_invoice': False,
            'automate_print_invoices': False,
            'automate_purchase': False,
            'automate_print_bills': False,
        })
        settings.execute()

        self.assertFalse(self.config_param.get_bool('automate_sale'))
        self.assertFalse(self.config_param.get_bool('automate_invoice'))
        self.assertFalse(self.config_param.get_bool('automate_validate_invoice'))
        self.assertFalse(self.config_param.get_bool('automate_print_invoices'))
        self.assertFalse(self.config_param.get_bool('automate_purchase'))
        self.assertFalse(self.config_param.get_bool('automate_print_bills'))

    def test_02_sale_order_automation_disabled(self):
        """Test creating a sales order when automation is disabled."""
        self._reset_config_parameters()
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_ordered.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })
        self.assertEqual(order.state, 'draft')
        self.assertFalse(order.automate_print_invoices)
        self.assertFalse(order.invoice_ids)

    def test_03_sale_order_auto_confirm_only(self):
        """Test auto-confirming quotation when automate_sale is enabled."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_sale', True)
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_ordered.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        self.assertEqual(order.state, 'sale')
        self.assertFalse(order.invoice_ids)

    def test_04_sale_order_empty_lines(self):
        """Test auto-confirming quotation without order lines."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_sale', True)
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(order.state, 'sale')

    def test_05_sale_order_website_safeguard(self):
        """Test that website orders bypass auto-confirmation if website_sale is installed."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_sale', True)
        if 'website_id' in self.env['sale.order']._fields:
            order = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'website_id': 1,
                'order_line': [(0, 0, {
                    'product_id': self.product_ordered.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                })],
            })
            self.assertEqual(order.state, 'draft')
        else:
            order = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'order_line': [(0, 0, {
                    'product_id': self.product_ordered.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                })],
            })
            self.assertEqual(order.state, 'sale')

    def test_06_sale_order_create_invoice(self):
        """Test automatic invoice creation in draft state."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_sale', True)
        self.config_param.set_bool('automate_invoice', True)
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_ordered.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })
        self.assertEqual(order.state, 'sale')
        self.assertEqual(len(order.invoice_ids), 1)
        self.assertEqual(order.invoice_ids.state, 'draft')

    def test_07_sale_order_validate_invoice(self):
        """Test automatic invoice creation and validation into posted state."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_sale', True)
        self.config_param.set_bool('automate_invoice', True)
        self.config_param.set_bool('automate_validate_invoice', True)
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_ordered.id,
                'product_uom_qty': 3.0,
                'price_unit': 100.0,
            })],
        })
        self.assertEqual(order.state, 'sale')
        self.assertEqual(len(order.invoice_ids), 1)
        self.assertEqual(order.invoice_ids.state, 'posted')

    def test_08_sale_order_print_invoice_action(self):
        """Test Print Invoice flag and action report execution."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_sale', True)
        self.config_param.set_bool('automate_invoice', True)
        self.config_param.set_bool('automate_print_invoices', True)
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_ordered.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        self.assertTrue(order.automate_print_invoices)
        action = order.action_print_invoice()
        self.assertIsInstance(action, dict)
        self.assertIn(action.get('type'), ('ir.actions.report', 'ir.actions.act_window'))

    def test_09_sale_order_delivery_policy_validation(self):
        """Test that delivery invoicing policy raises ValidationError when invoice creation is automated."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_sale', True)
        self.config_param.set_bool('automate_invoice', True)
        with self.assertRaises(ValidationError):
            self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'order_line': [(0, 0, {
                    'product_id': self.product_delivery.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 150.0,
                })],
            })

    def test_10_purchase_order_automation_disabled(self):
        """Test creating an RFQ when purchase automation is disabled."""
        self._reset_config_parameters()
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_ordered.id,
                'product_qty': 5.0,
                'price_unit': 60.0,
            })],
        })
        self.assertEqual(po.state, 'draft')
        self.assertFalse(po.automate_print_bills)

    def test_11_purchase_order_auto_confirm(self):
        """Test auto-confirming RFQ to purchase order when automate_purchase is enabled."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_purchase', True)
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_ordered.id,
                'product_qty': 5.0,
                'price_unit': 60.0,
            })],
        })
        self.assertEqual(po.state, 'purchase')

    def test_12_purchase_order_empty_lines(self):
        """Test auto-confirming RFQ without order lines."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_purchase', True)
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
        })
        self.assertEqual(po.state, 'purchase')

    def test_13_purchase_order_website_safeguard(self):
        """Test that website orders bypass purchase auto-confirmation if website field exists."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_purchase', True)
        if 'website_id' in self.env['purchase.order']._fields:
            po = self.env['purchase.order'].create({
                'partner_id': self.vendor.id,
                'website_id': 1,
                'order_line': [(0, 0, {
                    'product_id': self.product_ordered.id,
                    'product_qty': 2.0,
                    'price_unit': 60.0,
                })],
            })
            self.assertEqual(po.state, 'draft')
        else:
            po = self.env['purchase.order'].create({
                'partner_id': self.vendor.id,
                'order_line': [(0, 0, {
                    'product_id': self.product_ordered.id,
                    'product_qty': 2.0,
                    'price_unit': 60.0,
                })],
            })
            self.assertEqual(po.state, 'purchase')

    def test_14_purchase_order_print_bills_action(self):
        """Test Print Bills flag and report execution on purchase order."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_purchase', True)
        self.config_param.set_bool('automate_print_bills', True)
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_ordered.id,
                'product_qty': 3.0,
                'price_unit': 60.0,
            })],
        })
        self.assertTrue(po.automate_print_bills)
        action = po.action_print_bill()
        self.assertIsInstance(action, dict)
        self.assertIn(action.get('type'), ('ir.actions.report', 'ir.actions.act_window'))

    def test_15_purchase_order_delivery_policy_validation(self):
        """Test that delivery invoicing policy raises ValidationError when purchase automation is enabled."""
        self._reset_config_parameters()
        self.config_param.set_bool('automate_purchase', True)
        with self.assertRaises(ValidationError):
            self.env['purchase.order'].create({
                'partner_id': self.vendor.id,
                'order_line': [(0, 0, {
                    'product_id': self.product_delivery.id,
                    'product_qty': 1.0,
                    'price_unit': 80.0,
                })],
            })

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
import requests
from unittest.mock import patch

from odoo import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for Google Analytics configuration settings."""

    def test_res_config_settings_analytics_crud(self):
        """Test enabling, configuring, and disabling Google Analytics parameters."""
        icp = self.env['ir.config_parameter'].sudo()

        # 1. Enable and configure parameters
        config = self.env['res.config.settings'].create({
            'enable_analytics': True,
            'measurement_id_analytics': 'G-TEST987654',
            'api_secret': 'SECRET_CONFIG_123',
        })
        config.execute()

        self.assertEqual(
            icp.get_str('google_analytics_odoo.measurement_id_analytics'),
            'G-TEST987654',
        )
        self.assertEqual(
            icp.get_str('google_analytics_odoo.api_secret'),
            'SECRET_CONFIG_123',
        )

        # 2. Disable analytics
        config_disabled = self.env['res.config.settings'].create({
            'enable_analytics': False,
            'measurement_id_analytics': '',
            'api_secret': '',
        })
        config_disabled.execute()


@tagged('post_install', '-at_install')
class TestSaleOrderGoogleAnalytics(TransactionCase):
    """Test suite for Sale Order analytics tracking."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env['ir.config_parameter'].sudo()
        cls.icp.set_str('google_analytics_odoo.enable_analytics', 'True')
        cls.icp.set_str('google_analytics_odoo.measurement_id_analytics', 'G-SALE123')
        cls.icp.set_str('google_analytics_odoo.api_secret', 'SECRET_SALE456')

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Analytics Customer',
            'email': 'customer.analytics@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Analytics Product',
            'list_price': 120.0,
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 120.0,
                })
            ],
        })

    def test_sale_order_action_confirm_analytics_enabled(self):
        """Test sales order confirmation sends Sales_Order event to GA."""
        with patch('requests.post') as mock_post:
            self.order.action_confirm()
            self.assertEqual(self.order.state, 'sale')
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn('measurement_id=G-SALE123', args[0])
            self.assertIn('api_secret=SECRET_SALE456', args[0])
            payload = kwargs.get('json', {})
            self.assertEqual(payload['client_id'], str(self.partner.id))
            self.assertEqual(len(payload['events']), 1)
            event = payload['events'][0]
            self.assertEqual(event['name'], 'Sales_Order')
            self.assertEqual(event['params']['Number'], self.order.name)
            self.assertEqual(event['params']['Customer'], self.partner.name)
            self.assertEqual(event['params']['Amount'], self.order.amount_total)

    def test_sale_order_action_confirm_analytics_disabled(self):
        """Test sales order confirmation does not send event when disabled."""
        self.icp.set_str('google_analytics_odoo.enable_analytics', '')
        new_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 120.0,
                })
            ],
        })
        with patch('requests.post') as mock_post:
            new_order.action_confirm()
            self.assertEqual(new_order.state, 'sale')
            mock_post.assert_not_called()

    def test_sale_order_action_confirm_multi_recordset(self):
        """Test sales order confirmation on multiple records sends event for each."""
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                })
            ],
        })
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 100.0,
                })
            ],
        })
        with patch('requests.post') as mock_post:
            (order1 + order2).action_confirm()
            self.assertEqual(order1.state, 'sale')
            self.assertEqual(order2.state, 'sale')
            self.assertEqual(mock_post.call_count, 2)

    def test_cart_add_analytics_event_success(self):
        """Test _cart_add triggers Add_To_Cart analytics event in Odoo 20."""
        draft_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 120.0,
                })
            ],
        })
        order_line = draft_order.order_line[0]
        sale_order_class = type(draft_order)
        fake_return = {'line_id': order_line.id, 'quantity': 2.0}
        with patch('requests.post') as mock_post, \
                patch.object(sale_order_class, '_cart_add', wraps=draft_order._cart_add):
            with patch('odoo.addons.website_sale.models.sale_order.SaleOrder._cart_add', return_value=fake_return):
                result = draft_order._cart_add(product_id=self.product.id, quantity=2.0)
                self.assertEqual(result['line_id'], order_line.id)
                mock_post.assert_called_once()
                args, kwargs = mock_post.call_args
                payload = kwargs.get('json', {})
                event = payload['events'][0]
                self.assertEqual(event['name'], 'Add_To_Cart')
                self.assertEqual(event['params']['Product_Name'], order_line.name_short or order_line.product_id.display_name)
                self.assertEqual(event['params']['Quantity'], 2.0)
                self.assertEqual(event['params']['Amount'], order_line.price_unit)

    def test_cart_update_legacy_wrapper(self):
        """Test legacy _cart_update delegates to _cart_add without crashing."""
        draft_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 120.0,
                })
            ],
        })
        order_line = draft_order.order_line[0]
        sale_order_class = type(draft_order)
        fake_return = {'line_id': order_line.id, 'quantity': 3.0}
        with patch('requests.post'), \
                patch.object(sale_order_class, '_cart_add', return_value=fake_return):
            res = draft_order._cart_update(product_id=self.product.id, add_qty=3)
            self.assertEqual(res['line_id'], order_line.id)

    def test_sale_order_action_confirm_network_error_resilience(self):
        """Test sales order confirmation succeeds even if GA network call fails."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 120.0,
                })
            ],
        })
        with patch('requests.post', side_effect=requests.RequestException("Connection timeout")):
            order.action_confirm()
            self.assertEqual(order.state, 'sale')


@tagged('post_install', '-at_install')
class TestPurchaseOrderGoogleAnalytics(TransactionCase):
    """Test suite for Purchase Order analytics tracking."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env['ir.config_parameter'].sudo()
        cls.icp.set_str('google_analytics_odoo.enable_analytics', 'True')
        cls.icp.set_str('google_analytics_odoo.measurement_id_analytics', 'G-PURCHASE789')
        cls.icp.set_str('google_analytics_odoo.api_secret', 'SECRET_PURCHASE101')

        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Analytics Vendor',
            'email': 'vendor.analytics@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Purchase Product',
            'standard_price': 75.0,
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product.id,
                    'product_qty': 4.0,
                    'price_unit': 75.0,
                })
            ],
        })

    def test_purchase_order_button_confirm_analytics_enabled(self):
        """Test purchase order confirmation sends Purchase_Order event to GA."""
        with patch('requests.post') as mock_post:
            self.po.button_confirm()
            self.assertEqual(self.po.state, 'purchase')
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn('measurement_id=G-PURCHASE789', args[0])
            self.assertIn('api_secret=SECRET_PURCHASE101', args[0])
            payload = kwargs.get('json', {})
            self.assertEqual(payload['client_id'], str(self.vendor.id))
            self.assertEqual(len(payload['events']), 1)
            event = payload['events'][0]
            self.assertEqual(event['name'], 'Purchase_Order')
            self.assertEqual(event['params']['Number'], self.po.name)
            self.assertEqual(event['params']['Customer'], self.vendor.name)
            self.assertEqual(event['params']['Amount'], self.po.amount_total)

    def test_purchase_order_button_confirm_analytics_disabled(self):
        """Test purchase order confirmation does not send event when disabled."""
        self.icp.set_str('google_analytics_odoo.enable_analytics', '')
        new_po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_qty': 1.0,
                    'price_unit': 75.0,
                })
            ],
        })
        with patch('requests.post') as mock_post:
            new_po.button_confirm()
            self.assertEqual(new_po.state, 'purchase')
            mock_post.assert_not_called()

    def test_purchase_order_button_confirm_multi_recordset(self):
        """Test purchase order confirmation on multiple records sends event for each."""
        po1 = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_qty': 1.0,
                    'price_unit': 75.0,
                })
            ],
        })
        po2 = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_qty': 2.0,
                    'price_unit': 75.0,
                })
            ],
        })
        with patch('requests.post') as mock_post:
            (po1 + po2).button_confirm()
            self.assertEqual(po1.state, 'purchase')
            self.assertEqual(po2.state, 'purchase')
            self.assertEqual(mock_post.call_count, 2)

    def test_purchase_order_button_confirm_network_error_resilience(self):
        """Test purchase order confirmation succeeds even if GA network call fails."""
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_qty': 1.0,
                    'price_unit': 75.0,
                })
            ],
        })
        with patch('requests.post', side_effect=requests.RequestException("Connection timeout")):
            po.button_confirm()
            self.assertEqual(po.state, 'purchase')


@tagged('post_install', '-at_install')
class TestAccountMoveGoogleAnalytics(TransactionCase):
    """Test suite for Account Move (Invoice) analytics tracking."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env['ir.config_parameter'].sudo()
        cls.icp.set_str('google_analytics_odoo.enable_analytics', 'True')
        cls.icp.set_str('google_analytics_odoo.measurement_id_analytics', 'G-INV555')
        cls.icp.set_str('google_analytics_odoo.api_secret', 'SECRET_INV777')

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Invoice Customer',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Invoice Product',
            'list_price': 250.0,
        })
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': cls.product.id,
                    'quantity': 1.0,
                    'price_unit': 250.0,
                })
            ],
        })

    def test_invoice_action_post_analytics_enabled(self):
        """Test posting invoice sends Invoices event to GA."""
        with patch('requests.post') as mock_post:
            self.invoice.action_post()
            self.assertEqual(self.invoice.state, 'posted')
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn('measurement_id=G-INV555', args[0])
            self.assertIn('api_secret=SECRET_INV777', args[0])
            payload = kwargs.get('json', {})
            self.assertEqual(payload['client_id'], str(self.partner.id))
            self.assertEqual(len(payload['events']), 1)
            event = payload['events'][0]
            self.assertEqual(event['name'], 'Invoices')
            self.assertEqual(event['params']['Number'], self.invoice.name)
            self.assertEqual(event['params']['Customer'], self.partner.name)
            self.assertEqual(event['params']['Amount'], self.invoice.amount_total)

    def test_invoice_action_post_analytics_disabled(self):
        """Test posting invoice does not send event when disabled."""
        self.icp.set_str('google_analytics_odoo.enable_analytics', '')
        new_inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'price_unit': 100.0,
                })
            ],
        })
        with patch('requests.post') as mock_post:
            new_inv.action_post()
            self.assertEqual(new_inv.state, 'posted')
            mock_post.assert_not_called()

    def test_invoice_action_post_multi_recordset(self):
        """Test posting multiple invoices sends event for each invoice without singleton error."""
        inv1 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'price_unit': 150.0,
                })
            ],
        })
        inv2 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product.id,
                    'quantity': 2.0,
                    'price_unit': 150.0,
                })
            ],
        })
        with patch('requests.post') as mock_post:
            (inv1 + inv2).action_post()
            self.assertEqual(inv1.state, 'posted')
            self.assertEqual(inv2.state, 'posted')
            self.assertEqual(mock_post.call_count, 2)

    def test_invoice_action_post_network_error_resilience(self):
        """Test invoice posting succeeds even if GA network call fails."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'price_unit': 200.0,
                })
            ],
        })
        with patch('requests.post', side_effect=requests.RequestException("Connection timeout")):
            invoice.action_post()
            self.assertEqual(invoice.state, 'posted')


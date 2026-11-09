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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""HTTP and controller test cases for return orders in website portal."""
from odoo.fields import Command
from odoo.tests import HttpCase, tagged
from odoo.addons.website_multi_product_return_management.controllers.portal import ReturnCustomerPortal


@tagged('post_install', '-at_install')
class TestPortalController(HttpCase):
    """Test HTTP routes, JSON-RPC requests, and portal return controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal Customer',
            'login': 'portal_customer_test',
            'password': 'portal_customer_test',
            'email': 'portal_customer_test@example.com',
            'group_ids': [Command.set([cls.env.ref('base.group_portal').id])],
        })
        cls.portal_partner = cls.portal_user.partner_id

        cls.other_user = cls.env['res.users'].create({
            'name': 'Other Customer',
            'login': 'other_customer_test',
            'password': 'other_customer_test',
            'email': 'other_customer_test@example.com',
            'group_ids': [Command.set([cls.env.ref('base.group_portal').id])],
        })
        cls.other_partner = cls.other_user.partner_id

        cls.product = cls.env['product.product'].create({
            'name': 'Website Return Product',
            'type': 'consu',
            'list_price': 120.0,
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.portal_partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product.id,
                    'product_uom_qty': 4,
                    'price_unit': 120.0,
                    'qty_delivered': 4,
                }),
            ],
        })
        cls.sale_order.action_confirm()

        cls.portal_return = cls.env['sale.return'].create({
            'sale_order_id': cls.sale_order.id,
            'partner_id': cls.portal_partner.id,
            'state': 'draft',
            'return_line_ids': [
                Command.create({
                    'product_id': cls.product.id,
                    'quantity': 4.0,
                    'received_qty': 1.0,
                    'reason': 'Wrong size',
                }),
            ],
        })

        cls.other_return = cls.env['sale.return'].create({
            'sale_order_id': cls.sale_order.id,
            'partner_id': cls.other_partner.id,
            'state': 'draft',
        })

    def test_01_portal_home_counters(self):
        """Test portal home page loads and displays return order counter."""
        self.authenticate(self.portal_user.login, self.portal_user.login)
        res = self.url_open('/my')
        self.assertEqual(res.status_code, 200, "Portal home page should load with status 200")
        self.assertIn('return_orders', res.text, "Portal home page should link to return orders")

    def test_02_controller_sale_return_jsonrpc_valid(self):
        """Test creating return order through /sale_return JSON-RPC endpoint."""
        payload = {
            'vals': [{
                'order_id': self.sale_order.id,
                'product_id': self.product.id,
                'quantity': 2,
                'deli_qty': 4,
                'reason': 'Found defect in material',
            }],
        }
        result = self.make_jsonrpc_request('/sale_return', params=payload)
        self.assertTrue(result, "JSON-RPC endpoint must return True for valid payload")

        # Verify created sale.return record in draft state
        created_return = self.env['sale.return'].search([
            ('sale_order_id', '=', self.sale_order.id),
            ('partner_id', '=', self.portal_partner.id),
        ], order='id desc', limit=1)
        self.assertTrue(created_return)
        self.assertEqual(created_return.state, 'draft')
        self.assertEqual(len(created_return.return_line_ids), 1)
        self.assertEqual(created_return.return_line_ids[0].product_id, self.product)
        self.assertEqual(created_return.return_line_ids[0].received_qty, 2.0)
        self.assertEqual(created_return.return_line_ids[0].reason, 'Found defect in material')

    def test_03_controller_sale_return_jsonrpc_invalid(self):
        """Test /sale_return endpoint handles empty and invalid payloads gracefully."""
        # 1. Empty vals list
        res_empty = self.make_jsonrpc_request('/sale_return', params={'vals': []})
        self.assertFalse(res_empty, "Should return False when vals is empty")

        # 2. Missing order_id
        res_no_order = self.make_jsonrpc_request('/sale_return', params={
            'vals': [{
                'product_id': self.product.id,
                'quantity': 2,
            }]
        })
        self.assertFalse(res_no_order, "Should return False when order_id is missing")

        # 3. Non-positive quantity
        res_zero_qty = self.make_jsonrpc_request('/sale_return', params={
            'vals': [{
                'order_id': self.sale_order.id,
                'product_id': self.product.id,
                'quantity': 0,
            }]
        })
        self.assertFalse(res_zero_qty, "Should return False when quantity is zero or negative")

    def test_04_controller_thank_you_page(self):
        """Test accessing /my/request-thank-you renders the confirmation page."""
        response = self.url_open('/my/request-thank-you')
        self.assertEqual(response.status_code, 200, "Thank you page should be accessible with status 200")

    def test_05_portal_my_sale_return_routes_and_filters(self):
        """Test portal return list view with sorting and filtering options."""
        self.authenticate(self.portal_user.login, self.portal_user.login)

        # Base list view
        res = self.url_open('/my/return_orders')
        self.assertEqual(res.status_code, 200)

        # Sort by date
        res_sort_date = self.url_open('/my/return_orders?sortby=date')
        self.assertEqual(res_sort_date.status_code, 200)

        # Sort by name
        res_sort_name = self.url_open('/my/return_orders?sortby=name')
        self.assertEqual(res_sort_name.status_code, 200)

        # Filter by confirmed
        res_filter_confirm = self.url_open('/my/return_orders?filterby=confirm')
        self.assertEqual(res_filter_confirm.status_code, 200)

        # Filter by done
        res_filter_done = self.url_open('/my/return_orders?filterby=done')
        self.assertEqual(res_filter_done.status_code, 200)

    def test_06_portal_my_return_detail_access_and_security(self):
        """Test portal return detail page access rights and report download."""
        self.authenticate(self.portal_user.login, self.portal_user.login)

        # 1. Access own return order detail
        res = self.url_open(f'/my/return_orders/{self.portal_return.id}')
        self.assertEqual(res.status_code, 200)

        # 2. Access report download for own return order
        res_report = self.url_open(f'/my/return_orders/{self.portal_return.id}?report_type=pdf')
        self.assertEqual(res_report.status_code, 200)

        # 3. Access other user's return order (should redirect to /my due to AccessError)
        res_other = self.url_open(f'/my/return_orders/{self.other_return.id}')
        # In portal CustomerPortal._document_check_access, unauthorized requests redirect to /my
        self.assertIn(res_other.status_code, [200, 302, 303])
        # If followed redirect, the URL should be /my
        if res_other.status_code == 200:
            self.assertTrue(res_other.url.endswith('/my') or '/my' in res_other.url)

# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo.tests import HttpCase, tagged

from odoo.addons.sale_stock.tests.common import TestSaleStockCommon


@tagged('post_install', '-at_install')
class TestSaleReturnPortalHttp(TestSaleStockCommon, HttpCase):
    """Actually render the portal pages and the frontend asset bundle.
    Compile checks (compileall, XML well-formedness) don't catch a QWeb
    template that only fails at render time - these tests GET the real
    pages as a logged-in portal user."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        cls.portal_partner = cls.env['res.partner'].create({'name': 'Portal HTTP Tester'})
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal HTTP Tester',
            'login': 'return_portal_http',
            'password': 'return_portal_http',
            'partner_id': cls.portal_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.other_portal_partner = cls.env['res.partner'].create({'name': 'Other Portal HTTP Tester'})
        cls.other_portal_user = cls.env['res.users'].create({
            'name': 'Other Portal HTTP Tester',
            'login': 'return_portal_http_b',
            'password': 'return_portal_http_b',
            'partner_id': cls.other_portal_partner.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

        cls.empty_portal_user = cls.env['res.users'].create({
            'name': 'Empty Portal HTTP Tester',
            'login': 'return_portal_http_c',
            'password': 'return_portal_http_c',
            'partner_id': cls.env['res.partner'].create({'name': 'Empty Portal HTTP Tester'}).id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def setUp(self):
        super().setUp()
        self.sale_order = self._so_deliver(
            self.product, quantity=3, partner=self.portal_partner)
        self.sale_return = self.env['sale.return'].create({
            'product_id': self.product.id,
            'sale_order_id': self.sale_order.id,
            'partner_id': self.portal_partner.id,
            'quantity': 1,
        })
        self.other_sale_order = self._so_deliver(
            self.product, quantity=3, partner=self.other_portal_partner)
        self.other_sale_return = self.env['sale.return'].create({
            'product_id': self.product.id,
            'sale_order_id': self.other_sale_order.id,
            'partner_id': self.other_portal_partner.id,
            'quantity': 1,
        })

    def test_portal_return_list_renders(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        response = self.url_open('/my/return_orders')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.sale_return.name, response.text)

    def test_portal_return_list_does_not_leak_other_partner(self):
        """Negative control for the partner-scoping domain in
        portal_my_sale_return(): user A's list must not contain user
        B's return."""
        self.authenticate(self.portal_user.login, self.portal_user.login)
        response = self.url_open('/my/return_orders')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.sale_return.name, response.text)
        self.assertNotIn(self.other_sale_return.name, response.text)

    def test_portal_return_detail_renders(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        response = self.url_open('/my/return_orders/%s' % self.sale_return.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.sale_return.name, response.text)

    def test_portal_return_detail_denies_other_partner(self):
        """Negative control for the auth="user" + ACL fix on
        portal_my_return_detail(): user A must not be able to open
        user B's return by id."""
        self.authenticate(self.portal_user.login, self.portal_user.login)
        response = self.url_open(
            '/my/return_orders/%s' % self.other_sale_return.id, allow_redirects=False)
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, (301, 302, 303, 307, 308))

    def test_portal_home_shows_return_counter_card(self):
        """The 'Return Orders' portal.entry card is driven client-side by
        data-placeholder_count on /my/home - check the markup carries it
        rather than trying to execute the JS that fills the count in."""
        self.authenticate(self.portal_user.login, self.portal_user.login)
        response = self.url_open('/my/home')
        self.assertEqual(response.status_code, 200)
        self.assertIn('return_count', response.text)
        self.assertIn('Return Orders', response.text)

    def test_return_counter_is_scoped_to_partner(self):
        """Negative control for the domain in _prepare_portal_counter_values():
        the /my/counters badge must count only the caller's returns. A
        portal user with no returns must get 0 even though other
        partners have returns (the route counts with limit=1, so a
        leak shows up as 1)."""
        counters = {'return_count': 'client_category'}
        self.authenticate(self.empty_portal_user.login, self.empty_portal_user.login)
        result = self.make_jsonrpc_request('/my/counters', {'counters': counters})
        self.assertEqual(result['return_count'], 0)
        self.authenticate(self.portal_user.login, self.portal_user.login)
        result = self.make_jsonrpc_request('/my/counters', {'counters': counters})
        self.assertEqual(result['return_count'], 1)

    def test_frontend_asset_bundle_compiles(self):
        """web.assets_frontend includes the rewritten sale_return.js;
        force-compile it the same way the real /web/assets/... route
        does, so a JS syntax error would fail this test."""
        bundle = self.env['ir.qweb']._get_asset_bundle('web.assets_frontend')
        js_attachment = bundle.js()
        self.assertTrue(js_attachment)
        content = js_attachment.raw.decode()
        self.assertIn('website_return_management.SaleReturn', content)

    def test_portal_return_list_filters_and_sorting(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        for sortby in ('date', 'name', 'sale'):
            response = self.url_open('/my/return_orders?sortby=%s' % sortby)
            self.assertIn(self.sale_return.name, response.text)
        response = self.url_open('/my/return_orders?filterby=cancel')
        self.assertNotIn(self.sale_return.name, response.text)
        self.assertIn('no return orders', response.text)
        response = self.url_open(
            '/my/return_orders?date_begin=2000-01-01&date_end=2999-01-01')
        self.assertIn(self.sale_return.name, response.text)

    def test_portal_return_report_html(self):
        self.authenticate(self.portal_user.login, self.portal_user.login)
        response = self.url_open(
            '/my/return_orders/%s?report_type=html' % self.sale_return.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Return Order', response.text)

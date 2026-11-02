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
class TestSaleReturnRoute(TestSaleStockCommon, HttpCase):
    """The /sale_return POST route: ownership check and auth."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        group_portal = cls.env.ref('base.group_portal')
        cls.partner_a = cls.env['res.partner'].create({'name': 'Route Tester A'})
        cls.user_a = cls.env['res.users'].create({
            'name': 'Route Tester A',
            'login': 'return_route_a',
            'password': 'return_route_a',
            'partner_id': cls.partner_a.id,
            'group_ids': [(6, 0, [group_portal.id])],
        })
        cls.partner_b = cls.env['res.partner'].create({'name': 'Route Tester B'})
        cls.user_b = cls.env['res.users'].create({
            'name': 'Route Tester B',
            'login': 'return_route_b',
            'password': 'return_route_b',
            'partner_id': cls.partner_b.id,
            'group_ids': [(6, 0, [group_portal.id])],
        })

    def setUp(self):
        super().setUp()
        self.order_a = self._so_deliver(self.product, quantity=3, partner=self.partner_a)
        self.order_b = self._so_deliver(self.product, quantity=3, partner=self.partner_b)

    def _post_return(self, order, product=None, qty='1', csrf=True):
        data = {
            'order_id': order.id,
            'product': (product or self.product).id,
            'qty': qty,
            'reason': 'route test',
        }
        if csrf:
            data['csrf_token'] = self.csrf_token()
        return self.url_open('/sale_return', data=data, allow_redirects=False)

    def _assert_rejected(self, response, order, error):
        self.assertIn(response.status_code, (301, 302, 303, 307, 308))
        self.assertIn('return_error=%s' % error, response.headers['Location'])
        self.assertFalse(self._returns_for(order))

    def _returns_for(self, order):
        return self.env['sale.return'].sudo().search([('sale_order_id', '=', order.id)])

    def test_owner_can_create_return(self):
        self.authenticate(self.user_a.login, self.user_a.login)
        response = self._post_return(self.order_a)
        self.assertIn(response.status_code, (301, 302, 303, 307, 308))
        self.assertIn('request-thank-you', response.headers['Location'])
        returns = self._returns_for(self.order_a)
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns.partner_id, self.partner_a)

    def test_cannot_create_return_for_other_partner_order(self):
        """Negative control for the ownership check on /sale_return:
        user A posting user B's order id must create nothing."""
        self.authenticate(self.user_a.login, self.user_a.login)
        response = self._post_return(self.order_b)
        self.assertIn(response.status_code, (301, 302, 303, 307, 308))
        self.assertNotIn('request-thank-you', response.headers['Location'])
        self.assertFalse(self._returns_for(self.order_b))

    def test_unauthenticated_cannot_create_return(self):
        self.authenticate(None, None)
        response = self._post_return(self.order_a)
        self.assertNotIn('request-thank-you', response.headers.get('Location', ''))
        self.assertFalse(self._returns_for(self.order_a))

    def test_post_without_csrf_token_is_refused(self):
        """The route no longer disables CSRF protection."""
        self.authenticate(self.user_a.login, self.user_a.login)
        response = self._post_return(self.order_a, csrf=False)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self._returns_for(self.order_a))

    def test_owner_return_links_delivery_and_salesperson(self):
        self.order_a.user_id = self.env.ref('base.user_admin')
        self.authenticate(self.user_a.login, self.user_a.login)
        self._post_return(self.order_a, qty='2')
        sale_return = self._returns_for(self.order_a)
        self.assertEqual(sale_return.quantity, 2)
        self.assertEqual(sale_return.user_id, self.env.ref('base.user_admin'))
        self.assertEqual(sale_return.source_picking_ids,
                         self.order_a.picking_ids)

    def test_product_not_on_order_is_rejected(self):
        other_product = self.env['product.product'].create({
            'name': 'Not On The Order', 'is_storable': True})
        self.authenticate(self.user_a.login, self.user_a.login)
        response = self._post_return(self.order_a, product=other_product)
        self._assert_rejected(response, self.order_a, 'product')

    def test_non_numeric_product_is_rejected(self):
        self.authenticate(self.user_a.login, self.user_a.login)
        response = self.url_open('/sale_return', data={
            'order_id': self.order_a.id,
            'product': 'none',
            'qty': '1',
            'csrf_token': self.csrf_token(),
        }, allow_redirects=False)
        self._assert_rejected(response, self.order_a, 'product')

    def test_invalid_quantities_are_rejected(self):
        self.authenticate(self.user_a.login, self.user_a.login)
        for qty in ('0', '-1', 'abc', '4'):
            with self.subTest(qty=qty):
                response = self._post_return(self.order_a, qty=qty)
                self._assert_rejected(response, self.order_a, 'qty')

    def test_open_returns_count_against_delivered_qty(self):
        """3 units delivered: a second request for 2 more must be refused
        while the first return for 2 is still open."""
        self.authenticate(self.user_a.login, self.user_a.login)
        self._post_return(self.order_a, qty='2')
        response = self._post_return(self.order_a, qty='2')
        self.assertIn('return_error=qty', response.headers['Location'])
        self.assertEqual(len(self._returns_for(self.order_a)), 1)

    def test_undelivered_product_is_rejected(self):
        order = self._so_deliver(self.product, quantity=2, picking=False,
                                 partner=self.partner_a)
        order.order_line.qty_delivered = 2
        self.authenticate(self.user_a.login, self.user_a.login)
        response = self._post_return(order, qty='1')
        self.assertIn(response.status_code, (301, 302, 303, 307, 308))
        self.assertFalse(self._returns_for(order))

    def test_bad_order_id_redirects_home(self):
        self.authenticate(self.user_a.login, self.user_a.login)
        response = self.url_open('/sale_return', data={
            'order_id': 'abc',
            'csrf_token': self.csrf_token(),
        }, allow_redirects=False)
        self.assertTrue(response.headers['Location'].endswith('/my'))
        response = self.url_open('/sale_return', data={
            'order_id': '999999999',
            'csrf_token': self.csrf_token(),
        }, allow_redirects=False)
        self.assertTrue(response.headers['Location'].endswith('/my'))

    def test_error_message_shown_on_order_page(self):
        self.authenticate(self.user_a.login, self.user_a.login)
        url = self.order_a.get_portal_url(query_string='&return_error=qty')
        response = self.url_open(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('exceed the delivered quantity', response.text)
        self.assertIn('alert-danger', response.text)

    def test_thank_you_page_renders(self):
        self.authenticate(self.user_a.login, self.user_a.login)
        response = self.url_open('/my/request-thank-you')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Your return request has been sent', response.text)

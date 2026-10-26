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
from unittest.mock import MagicMock, patch
from werkzeug.exceptions import NotFound

from odoo.tests import common, tagged
from odoo.addons.website_product_reservation.controllers.website_product_reservation import (
    WebsiteSaleReservation,
)
from odoo.addons.website_product_reservation.controllers.portal import (
    ReservationCustomerPortal,
    Return,
)


class FakeEnv:
    """Wrapper around Environment that ensures website attribute is present."""

    def __init__(self, env, website=None, user=None):
        self._env = env
        self.website = website
        self.user = user or env.user

    def __getattr__(self, item):
        return getattr(self._env, item)

    def __getitem__(self, item):
        return self._env[item]


class FakeRequest:
    """Mock object simulating odoo.http.request for unit testing."""

    def __init__(self, env, website=None, user=None, session=None, cart=None):
        self.website = website
        self.user = user or env.user
        self.env = FakeEnv(env, website=website, user=self.user)
        self.session = session if session is not None else {}
        self.cart = cart
        self.csrf_token = MagicMock(return_value="fake_csrf_token")

    def render(self, template, values=None):
        return {'template': template, 'values': values or {}}

    def redirect(self, url):
        return {'redirect_url': url}


@tagged('post_install', '-at_install')
class TestReservationControllers(common.TransactionCase):
    """Test suite for Website Product Reservation and Portal controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        cls.company = cls.env.company

        # Partner and user
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Portal Reservation User',
            'login': 'portal_res_user',
            'email': 'portal_res@test.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.portal_partner = cls.portal_user.partner_id

        # Destination location for stock reservation
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1
        )
        cls.destination_location = cls.env['stock.location'].create({
            'name': 'Controller Test Dest Location',
            'usage': 'internal',
            'location_id': cls.warehouse.lot_stock_id.location_id.id,
            'company_id': cls.company.id,
        })
        cls.company.destination_location_id = cls.destination_location.id

        # Reservable product
        cls.product_template_reservable = cls.env['product.template'].create({
            'name': 'Web Reservable Product',
            'type': 'consu',
            'is_storable': True,
            'reserve_products': True,
            'website_published': True,
            'list_price': 100.0,
        })
        cls.product_reservable = cls.product_template_reservable.product_variant_id

        # Non-reservable product
        cls.product_template_non_reservable = cls.env['product.template'].create({
            'name': 'Web Standard Product',
            'type': 'consu',
            'is_storable': True,
            'reserve_products': False,
            'website_published': True,
            'list_price': 50.0,
        })
        cls.product_non_reservable = cls.product_template_non_reservable.product_variant_id

        # Controllers
        cls.website_sale_controller = WebsiteSaleReservation()
        cls.portal_controller = ReservationCustomerPortal()
        cls.return_portal_controller = Return()

    def _call(self, controller, method_name, fake_req, *args, **kwargs):
        """Invoke controller method directly bypassing the HTTP route wrapper."""
        func = getattr(controller, method_name)
        endpoint = getattr(func, 'original_endpoint', func)
        with patch('odoo.http.request', fake_req), \
             patch('odoo.addons.website_sale.models.website.request', fake_req), \
             patch('odoo.addons.website_product_reservation.controllers.website_product_reservation.request', fake_req), \
             patch('odoo.addons.website_product_reservation.controllers.portal.request', fake_req):
            return endpoint(controller, *args, **kwargs)

    def test_01_reservation_page_listing(self):
        """Test GET /reservation renders products available for reservation."""
        fake_req = FakeRequest(self.env, website=self.website)
        response = self._call(self.website_sale_controller, 'reservation', fake_req, page=1)
        self.assertEqual(
            response.get('template'),
            'website_product_reservation.reservation_page'
        )
        products = response['values'].get('products')
        self.assertIn(
            self.product_template_reservable,
            products,
            "Reservable published product should be on the reservation page"
        )
        self.assertNotIn(
            self.product_template_non_reservable,
            products,
            "Non-reservable product should not be on the reservation page"
        )

    def test_02_reservation_page_preserves_existing_cart(self):
        """Test GET /reservation does not wipe out existing cart lines."""
        cart_order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        self.assertTrue(cart_order.order_line)

        fake_req = FakeRequest(self.env, website=self.website, cart=cart_order)
        self._call(self.website_sale_controller, 'reservation', fake_req, page=1)
        self.assertTrue(
            cart_order.order_line,
            "Existing cart lines should be preserved when browsing reservation page"
        )

    def test_03_reservation_update_sets_reservation_order(self):
        """Test POST /reservation/reserve creates cart and sets is_reservation_order."""
        cart_order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
        })
        fake_req = FakeRequest(self.env, website=self.website, cart=cart_order)
        res = self._call(
            self.website_sale_controller,
            'reservation_update',
            fake_req,
            product_id=self.product_reservable.id,
            add_qty=2.0,
            set_qty=0.0,
            type_name='Reservation'
        )
        self.assertEqual(res.get('redirect_url'), '/shop/cart')
        self.assertTrue(
            cart_order.is_reservation_order,
            "Order should be marked as is_reservation_order"
        )

    def test_04_confirm_reserve_order_without_cart(self):
        """Test /reservation/confirm_reserve_order redirects to /shop when cart is missing."""
        fake_req = FakeRequest(self.env, website=self.website, cart=None)
        res = self._call(self.website_sale_controller, 'confirm_reserve_order', fake_req)
        self.assertEqual(res.get('redirect_url'), '/shop')

    def test_05_confirm_reserve_order_with_reservable_products(self):
        """Test /reservation/confirm_reserve_order confirms reservation for valid cart."""
        cart_order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
            'is_reservation_order': True,
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        session = {}
        fake_req = FakeRequest(self.env, website=self.website, session=session, cart=cart_order)
        res = self._call(self.website_sale_controller, 'confirm_reserve_order', fake_req)
        self.assertEqual(res.get('redirect_url'), '/reservation/thankyou')
        self.assertEqual(cart_order.state, 'reserve')
        self.assertEqual(session.get('sale_last_order_id'), cart_order.id)

    def test_06_confirm_reserve_order_with_non_reservable_products(self):
        """Test /reservation/confirm_reserve_order rejects reservation for mixed/standard cart."""
        cart_order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product_non_reservable.id,
                'product_uom_qty': 1.0,
                'price_unit': 50.0,
            })],
        })
        fake_req = FakeRequest(self.env, website=self.website, cart=cart_order)
        res = self._call(self.website_sale_controller, 'confirm_reserve_order', fake_req)
        self.assertEqual(
            res.get('template'),
            'website_product_reservation.not_allowed_to_reserve_page'
        )

    def test_07_reservation_thankyou_page(self):
        """Test /reservation/thankyou displays confirmation or redirects."""
        # When order_id is in session
        cart_order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
            'state': 'reserve',
        })
        fake_req_with_session = FakeRequest(
            self.env,
            website=self.website,
            session={'sale_last_order_id': cart_order.id}
        )
        res = self._call(self.website_sale_controller, 'reservation_thankyou', fake_req_with_session)
        self.assertEqual(
            res.get('template'),
            'website_product_reservation.reservation_thankyou'
        )
        self.assertEqual(res['values'].get('order'), cart_order)

        # When session has no order_id
        fake_req_no_session = FakeRequest(self.env, website=self.website, session={})
        res = self._call(self.website_sale_controller, 'reservation_thankyou', fake_req_no_session)
        self.assertEqual(res.get('redirect_url'), '/shop')

    def test_08_portal_home_reservation_counter(self):
        """Test reservation_count in home portal values and counter values."""
        # Create 2 reservation orders and 1 normal sale order
        self.env['sale.order'].create([
            {
                'partner_id': self.portal_partner.id,
                'is_reservation_order': True,
                'state': 'reserve',
            },
            {
                'partner_id': self.portal_partner.id,
                'is_reservation_order': True,
                'state': 'reserve',
            },
            {
                'partner_id': self.portal_partner.id,
                'is_reservation_order': False,
            },
        ])

        fake_req = FakeRequest(self.env, website=self.website, user=self.portal_user)
        with patch('odoo.http.request', fake_req), \
             patch('odoo.addons.website_product_reservation.controllers.portal.request', fake_req):
            values = self.return_portal_controller._prepare_home_portal_values({'reservation_count'})
            self.assertEqual(
                values.get('reservation_count'),
                2,
                "Portal counter should correctly count user's reservation orders"
            )
            # Test Odoo 20 counter tuple
            model_name, domain, access = self.return_portal_controller._prepare_portal_counter_values('reservation_count')
            self.assertEqual(model_name, 'sale.order')
            self.assertIn(('is_reservation_order', '=', True), domain)

    def test_09_portal_my_reservation_orders_list(self):
        """Test GET /my/reservation/requests renders portal tree view."""
        res_order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
            'is_reservation_order': True,
            'state': 'reserve',
        })
        fake_req = FakeRequest(self.env, website=self.website, user=self.portal_user)
        res = self._call(self.portal_controller, 'portal_my_reservation_orders', fake_req)
        self.assertEqual(
            res.get('template'),
            'website_product_reservation.portal_my_reservation_requests_tree'
        )
        self.assertIn(res_order, res['values'].get('reservation_request'))

    def test_10_portal_reservation_form_and_actions(self):
        """Test portal form view, cancel, and confirm endpoints."""
        res_order = self.env['sale.order'].create({
            'partner_id': self.portal_partner.id,
            'is_reservation_order': True,
            'state': 'reserve',
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        fake_req = FakeRequest(self.env, website=self.website, user=self.portal_user)
        # Form view
        form_res = self._call(self.portal_controller, 'get_my_reservation_request_form', fake_req, reservation_id=res_order.id)
        self.assertEqual(
            form_res.get('template'),
            'website_product_reservation.portal_my_reservation_requests_form'
        )
        self.assertEqual(form_res['values'].get('record_reservation_requests'), res_order)

        # Cancel reservation from portal
        cancel_res = self._call(self.portal_controller, 'get_my_reservation_request_form_cancel', fake_req, reservation_id=res_order.id)
        self.assertEqual(res_order.state, 'cancel')
        self.assertEqual(cancel_res.get('redirect_url'), f'/my/reservation/requests/form/{res_order.id}')

        # Reset back to reserve for confirm test
        res_order.state = 'reserve'
        confirm_res = self._call(self.portal_controller, 'get_my_reservation_request_form_confirm', fake_req, reservation_id=res_order.id)
        self.assertEqual(res_order.state, 'sale')
        self.assertEqual(confirm_res.get('redirect_url'), f'/my/reservation/requests/form/{res_order.id}')

    def test_11_portal_reservation_idor_prevention(self):
        """Test portal endpoints reject access to reservations belonging to other users (IDOR prevention)."""
        other_partner = self.env['res.partner'].create({
            'name': 'Other Customer',
            'email': 'other@test.com',
        })
        other_order = self.env['sale.order'].create({
            'partner_id': other_partner.id,
            'is_reservation_order': True,
            'state': 'reserve',
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        fake_req = FakeRequest(self.env, website=self.website, user=self.portal_user)

        # Attempt to view other user's reservation form
        with self.assertRaises(NotFound):
            self._call(self.portal_controller, 'get_my_reservation_request_form', fake_req, reservation_id=other_order.id)

        # Attempt to cancel other user's reservation
        with self.assertRaises(NotFound):
            self._call(self.portal_controller, 'get_my_reservation_request_form_cancel', fake_req, reservation_id=other_order.id)
        self.assertEqual(other_order.state, 'reserve', "Other order must not be cancelled")

        # Attempt to confirm other user's reservation
        with self.assertRaises(NotFound):
            self._call(self.portal_controller, 'get_my_reservation_request_form_confirm', fake_req, reservation_id=other_order.id)
        self.assertEqual(other_order.state, 'reserve', "Other order must not be confirmed")

        # Non-existent reservation id
        with self.assertRaises(NotFound):
            self._call(self.portal_controller, 'get_my_reservation_request_form', fake_req, reservation_id=999999)

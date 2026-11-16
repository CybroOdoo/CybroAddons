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
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError
from odoo.addons.google_analytics_odoo.controllers.checkout_payment_details import (
    CheckoutAndPayments,
)
from odoo.addons.google_analytics_odoo.controllers.login import Login
from odoo.addons.google_analytics_odoo.controllers.sign_up import (
    AnalyticsSignUp,
)
from odoo.addons.google_analytics_odoo.controllers.wishlist import (
    SaleWishlist,
)
from odoo.addons.website_sale.tests.common import MockRequest
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGoogleAnalyticsControllers(TransactionCase):
    """Test suite for Google Analytics frontend and authentication controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.icp = cls.env['ir.config_parameter'].sudo()
        cls.icp.set_str('google_analytics_odoo.enable_analytics', 'True')
        cls.icp.set_str('google_analytics_odoo.measurement_id_analytics', 'G-CTRL123')
        cls.icp.set_str('google_analytics_odoo.api_secret', 'SECRET_CTRL456')

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Controller User',
            'email': 'controller.test@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Controller Product',
            'list_price': 99.0,
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 99.0,
                })
            ],
        })

    def test_01_login_controller_analytics(self):
        """Test web_login sends Login_Information event when login succeeds."""
        controller = Login()
        with MockRequest(self.env) as req, patch('requests.post') as mock_post, \
                patch('odoo.addons.web.controllers.home.Home.web_login', return_value="login_redirect"):
            req.params['login_success'] = True
            res = controller.web_login(redirect=None, login='test_user')
            self.assertEqual(res.get_data(as_text=True), "login_redirect")
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            event = kwargs['json']['events'][0]
            self.assertEqual(event['name'], 'Login_Information')
            self.assertEqual(event['params']['User_login'], 'test_user')

    def test_02_signup_controller_analytics(self):
        """Test _signup_with_values sends Signup_Information event."""
        controller = AnalyticsSignUp()
        with MockRequest(self.env) as _req, patch('requests.post') as mock_post, \
                patch('odoo.addons.auth_signup.controllers.main.AuthSignupHome._signup_with_values', return_value=True):
            res = controller._signup_with_values('token123', {'login': 'new_user'}, True)
            self.assertTrue(res)
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            event = kwargs['json']['events'][0]
            self.assertEqual(event['name'], 'Signup_Information')

    def test_03_wishlist_controller_analytics(self):
        """Test add_to_wishlist sends Add_To_Wishlist event."""
        controller = SaleWishlist()
        with MockRequest(self.env) as _req, patch('requests.post') as mock_post, \
                patch('odoo.addons.website_sale.controllers.wishlist.ProductWishlist.add_to_wishlist', return_value=True):
            res = controller.add_to_wishlist(self.product.id)
            self.assertTrue(res)
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            event = kwargs['json']['events'][0]
            self.assertEqual(event['name'], 'Add_To_Wishlist')
            self.assertEqual(event['params']['Product_Name'], self.product.name)

    def test_03b_wishlist_controller_access_denied(self):
        """Test add_to_wishlist does not send GA event when access check fails."""
        controller = SaleWishlist()
        with MockRequest(self.env) as _req, patch('requests.post') as mock_post, \
                patch('odoo.addons.website_sale.controllers.wishlist.ProductWishlist.add_to_wishlist', return_value=True), \
                patch.object(type(self.env['product.product']), 'check_access', side_effect=AccessError("Access Denied")):
            controller.add_to_wishlist(self.product.id)
            mock_post.assert_not_called()

    def test_04_cart_checkout_controller_analytics(self):
        """Test shop_payment sends Cart_Checkout event."""
        controller = CheckoutAndPayments()
        with MockRequest(self.env) as req, patch('requests.post') as mock_post, \
                patch('odoo.addons.website_sale.controllers.main.WebsiteSale.shop_payment', return_value="checkout_view"):
            req.session['sale_order_id'] = self.order.id
            res = controller.shop_payment()
            self.assertEqual(res.get_data(as_text=True), "checkout_view")
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            event = kwargs['json']['events'][0]
            self.assertEqual(event['name'], 'Cart_Checkout')

    def test_05_online_payments_confirmation_controller_analytics(self):
        """Test shop_payment_confirmation sends Online_payments event."""
        controller = CheckoutAndPayments()
        with MockRequest(self.env) as req, patch('requests.post') as mock_post, \
                patch('odoo.addons.website_sale.controllers.main.WebsiteSale.shop_payment_confirmation', return_value="confirmation_view"):
            req.session['sale_last_order_id'] = self.order.id
            res = controller.shop_payment_confirmation()
            self.assertEqual(res.get_data(as_text=True), "confirmation_view")
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            event = kwargs['json']['events'][0]
            self.assertEqual(event['name'], 'Online_payments')


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
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.website_sale.controllers.main import WebsiteSale as BaseWebsiteSale
from odoo.addons.refer_friend_and_earn.controllers.refer_friend_and_earn import (
    WebsiteLogin,
    ReferAndEarn,
    WebsiteSale,
)
from odoo.http import request_var
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestWebsiteLogin(TransactionCase):
    """Test suite for WebsiteLogin controller methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.referrer_partner = cls.env['res.partner'].create({
            'name': 'Referrer Partner',
            'email': 'referrer@example.com',
            'referral_code': 'REFCODE77',
            'points': 20,
            'sign_up': 2,
        })
        cls.env['ir.config_parameter'].sudo().set_str(
            'refer_friend_and_earn.sign_up_points', '10')

    def test_get_auth_signup_qcontext(self):
        """Test get_auth_signup_qcontext includes referral_code when provided in request.params."""
        controller = WebsiteLogin()
        mock_req = MagicMock()
        with patch('odoo.addons.refer_friend_and_earn.controllers.refer_friend_and_earn.request', new=mock_req):
            # 1. When referral_code is present in request params
            mock_req.params = {'referral_code': 'REFCODE77'}
            with patch.object(AuthSignupHome, 'get_auth_signup_qcontext', return_value={'login': 'new_user'}):
                qcontext = controller.get_auth_signup_qcontext()
                self.assertEqual(qcontext.get('referral_code'), 'REFCODE77')

            # 2. When referral_code is not present in request params
            mock_req.params = {}
            with patch.object(AuthSignupHome, 'get_auth_signup_qcontext', return_value={'login': 'new_user'}):
                qcontext = controller.get_auth_signup_qcontext()
                self.assertNotIn('referral_code', qcontext)

    def test_do_signup(self):
        """Test do_signup awards points and increments sign_up count to the referrer."""
        controller = WebsiteLogin()
        initial_points = self.referrer_partner.points
        initial_sign_up = self.referrer_partner.sign_up

        mock_req = MagicMock()
        with patch('odoo.addons.refer_friend_and_earn.controllers.refer_friend_and_earn.request', new=mock_req):
            mock_req.env = self.env
            mock_req.params = {}

            with patch.object(AuthSignupHome, 'do_signup', return_value=True):
                # 1. Signup with valid referral code
                qcontext = {'referral_code': 'REFCODE77', 'login': 'friend1@example.com'}
                controller.do_signup(qcontext)
                self.referrer_partner.invalidate_recordset()
                self.assertEqual(self.referrer_partner.points, initial_points + 10)
                self.assertEqual(self.referrer_partner.sign_up, initial_sign_up + 1)

                # 2. Signup without referral code - points and sign_up remain unchanged
                controller.do_signup({'login': 'friend2@example.com'})
                self.referrer_partner.invalidate_recordset()
                self.assertEqual(self.referrer_partner.points, initial_points + 10)
                self.assertEqual(self.referrer_partner.sign_up, initial_sign_up + 1)

                # 3. Signup with invalid/non-existent referral code - points remain unchanged
                controller.do_signup({'referral_code': 'NON_EXISTENT_CODE'})
                self.referrer_partner.invalidate_recordset()
                self.assertEqual(self.referrer_partner.points, initial_points + 10)
                self.assertEqual(self.referrer_partner.sign_up, initial_sign_up + 1)


@tagged('post_install', '-at_install')
class TestReferAndEarn(TransactionCase):
    """Test suite for ReferAndEarn controller methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'Referral Test User',
            'login': 'referral_test_user_unique',
            'email': 'referral_user@example.com',
        })
        cls.mail_template = cls.env.ref(
            'refer_friend_and_earn.mail_template_refer_and_earn'
        )

    def test_refer_earn(self):
        """Test refer_earn generates a 7-character code for new user or reuses existing code."""
        controller = ReferAndEarn()
        mock_req = MagicMock()
        with patch('odoo.addons.refer_friend_and_earn.controllers.refer_friend_and_earn.request', new=mock_req):
            mock_req.env = self.env(user=self.user)
            mock_req.render = MagicMock(return_value='rendered_refer_earn')

            # Ensure partner has no referral code initially
            self.user.partner_id.referral_code = False
            self.user.partner_id.points = 50
            self.user.partner_id.sign_up = 4

            # 1. First execution: should generate a new 7-digit alphanumeric code
            controller.refer_earn()
            generated_code = self.user.partner_id.referral_code
            self.assertTrue(generated_code)
            self.assertEqual(len(generated_code), 7)
            mock_req.render.assert_called_with('refer_friend_and_earn.refer_earn_template', {
                'codes': generated_code,
                'points': 50,
                'sign_up': 4,
            })

            # 2. Second execution: should keep the already existing code
            controller.refer_earn()
            self.assertEqual(self.user.partner_id.referral_code, generated_code)

    def test_refer_and_earn_popup(self):
        """Test refer_and_earn_popup sends referral email and renders success template."""
        controller = ReferAndEarn()
        mock_req = MagicMock()
        with patch('odoo.addons.refer_friend_and_earn.controllers.refer_friend_and_earn.request', new=mock_req):
            mock_req.env = self.env(user=self.user)
            mock_req.render = MagicMock(return_value='rendered_success_page')

            with patch.object(type(self.mail_template), 'send_mail') as mock_send_mail:
                controller.refer_and_earn_popup(
                    referral_code='MYREF12',
                    email='invited_friend@example.com'
                )
                self.assertTrue(mock_send_mail.called)
                args, kwargs = mock_send_mail.call_args
                self.assertEqual(args[0], self.user.partner_id.id)
                self.assertEqual(kwargs['email_values']['email_to'], 'invited_friend@example.com')
                self.assertIn('MYREF12', kwargs['email_values']['body_html'])
                mock_req.render.assert_called_with('refer_friend_and_earn.website_success_page', {})


@tagged('post_install', '-at_install')
class TestWebsiteSale(TransactionCase):
    """Test suite for WebsiteSale controller referral discount methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.discount_product = cls.env['product.product'].sudo().search(
            [('default_code', '=', 'DISCOUNT001')], limit=1)
        if not cls.discount_product:
            cls.discount_product = cls.env['product.product'].sudo().create({
                'name': 'Discount',
                'default_code': 'DISCOUNT001',
                'type': 'service',
                'list_price': 0.0,
            })

        cls.user = cls.env['res.users'].create({
            'name': 'Shopping Referral User',
            'login': 'shopping_referral_user',
            'email': 'shopper@example.com',
        })
        cls.user.partner_id.points = 100

        cls.discount_rule = cls.env['apply.discounts'].create({
            'starting_points': 10,
            'end_points': 50,
            'discount': 10.0,
        })

        cls.regular_product = cls.env['product.product'].create({
            'name': 'Referral Store Item',
            'list_price': 200.0,
            'type': 'consu',
        })

    def _create_cart_order(self):
        """Helper to create a sale order with one regular item."""
        order = self.env['sale.order'].create({
            'partner_id': self.user.partner_id.id,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.regular_product.id,
            'product_uom_qty': 1,
            'price_unit': 200.0,
        })
        return order

    def test_refer_earn(self):
        """Test WebsiteSale.refer_earn applying discount based on secured points."""
        controller = WebsiteSale()
        order = self._create_cart_order()

        mock_req = MagicMock()
        with patch('odoo.addons.refer_friend_and_earn.controllers.refer_friend_and_earn.request', new=mock_req):
            mock_req.env = self.env(user=self.user)
            mock_req.cart = order
            mock_req.render = MagicMock(return_value='rendered_lack_of_points')
            mock_req.redirect = MagicMock(return_value='redirect_cart')

            # 1. Partner has insufficient points
            res = controller.refer_earn(points='150')
            mock_req.render.assert_called_with('refer_friend_and_earn.lack_of_points_template', {})

            # 2. Points don't match any discount rule
            res = controller.refer_earn(points='5')
            mock_req.render.assert_called_with('refer_friend_and_earn.lack_of_points_template', {})

            # 3. Valid points matching discount_rule (30 pts -> 10% discount on 200 = 20)
            res = controller.refer_earn(points='30', r='/shop/cart')
            self.assertEqual(order.discount_applied, 10.0)
            self.assertEqual(order.points_applied, 30.0)

            discount_line = order.order_line.filtered(
                lambda l: l.product_id.id == self.discount_product.id
            )
            self.assertTrue(discount_line)
            self.assertEqual(discount_line.price_unit, -20.0)
            mock_req.redirect.assert_called_with('/shop/cart')

    def test_cart_update_json(self):
        """Test cart_update_json recalculates discount line when cart items change."""
        controller = WebsiteSale()
        order = self._create_cart_order()
        order.discount_applied = 10.0

        # Add discount line
        discount_line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.discount_product.id,
            'product_uom_qty': 1,
            'price_unit': -20.0,
        })

        mock_req = MagicMock()
        token = request_var.set(mock_req)
        try:
            with patch('odoo.addons.refer_friend_and_earn.controllers.refer_friend_and_earn.request', new=mock_req):
                mock_req.env = self.env
                mock_req.cart = order
                mock_req.httprequest.url = '/shop/cart'

                with patch.object(BaseWebsiteSale, 'cart_update_json', create=True, return_value={}):
                    # Simulate increasing regular product quantity to 2 (total original: 400, discount should become -40)
                    regular_line = order.order_line.filtered(
                        lambda l: l.product_id.id == self.regular_product.id
                    )
                    regular_line.product_uom_qty = 2

                    endpoint = getattr(controller.cart_update_json, 'original_endpoint', controller.cart_update_json)
                    endpoint(controller)
                    discount_line.invalidate_recordset()
                    self.assertEqual(discount_line.price_unit, -40.0)
        finally:
            request_var.reset(token)

    def test_shop_payment_confirmation(self):
        """Test shop_payment_confirmation deducts applied points from the partner's balance."""
        controller = WebsiteSale()
        order = self._create_cart_order()
        order.points_applied = 30.0
        self.user.partner_id.points = 100

        mock_req = MagicMock()
        token = request_var.set(mock_req)
        try:
            with patch('odoo.addons.refer_friend_and_earn.controllers.refer_friend_and_earn.request', new=mock_req):
                mock_req.env = self.env(user=self.user)
                mock_req.session = {'sale_last_order_id': order.id}

                with patch.object(BaseWebsiteSale, 'shop_payment_confirmation', return_value='payment_confirmed'):
                    endpoint = getattr(controller.shop_payment_confirmation, 'original_endpoint', controller.shop_payment_confirmation)
                    res = endpoint(controller)
                    self.user.partner_id.invalidate_recordset()
                    self.assertEqual(self.user.partner_id.points, 70.0)
                    self.assertEqual(res, 'payment_confirmed')
        finally:
            request_var.reset(token)

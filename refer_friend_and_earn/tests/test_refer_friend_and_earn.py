# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#############################################################################
import odoo.http
import werkzeug
from unittest.mock import MagicMock, patch
from odoo.tests import TransactionCase, tagged
from odoo.addons.refer_friend_and_earn.controllers.refer_friend_and_earn import WebsiteLogin, ReferAndEarn, WebsiteSale


@tagged('post_install', '-at_install')
class TestReferFriendAndEarn(TransactionCase):
    """Test refer_friend_and_earn controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.WebsiteLogin = WebsiteLogin()
        cls.ReferAndEarn = ReferAndEarn()
        cls.WebsiteSale = WebsiteSale()
        
        cls.env['ir.config_parameter'].sudo().set_param('refer_friend_and_earn.sign_up_points', '50')
        cls.env['ir.config_parameter'].sudo().set_param('web.base.url', 'http://localhost:8069')
        
        cls.referrer_partner = cls.env['res.partner'].create({
            'name': 'Referrer Partner',
            'referral_code': 'ABCDEFG',
            'points': 100,
            'sign_up': 0
        })
        
        cls.user = cls.env['res.users'].create({
            'name': 'Referrer User',
            'login': 'referrer@test.com',
            'partner_id': cls.referrer_partner.id,
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])]
        })
        
        discount_product = cls.env['product.product'].search([('default_code', '=', 'DISCOUNT001')], limit=1)
        if discount_product:
            cls.discount_product = discount_product
        else:
            cls.discount_product = cls.env['product.product'].create({
                'name': 'Discount Product',
                'default_code': 'DISCOUNT001',
                'list_price': 0,
                'type': 'service'
            })
        
        cls.apply_discount = cls.env['apply.discounts'].create({
            'starting_points': 50,
            'end_points': 150,
            'discount': 10.0
        })
        
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100,
        })
        
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.referrer_partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 1,
                'price_unit': 100
            })]
        })

    def setUp(self):
        super().setUp()
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        self.mock_request.session = MagicMock()
        self.mock_request.session.uid = self.user.id
        self.mock_request.httprequest = MagicMock()
        self.mock_request.httprequest.method = 'POST'
        self.mock_request.website = MagicMock()
        self.mock_request.website.sale_get_order.return_value = self.sale_order
        self.mock_request.cookies = {}
        self.mock_request.render.return_value = werkzeug.wrappers.Response("Mocked Render")
        self.mock_request.redirect.return_value = werkzeug.wrappers.Response("Mocked Redirect")
        odoo.http._request_stack.push(self.mock_request)

    def tearDown(self):
        odoo.http._request_stack.pop()
        super().tearDown()

    @patch('odoo.addons.auth_signup.controllers.main.AuthSignupHome._prepare_signup_values')
    def test_prepare_signup_values(self, mock_super):
        """Test _prepare_signup_values adds points and signup count."""
        mock_super.return_value = {}
        qcontext = {'referral_code': 'ABCDEFG'}
        
        self.WebsiteLogin._prepare_signup_values(qcontext)
        
        self.assertEqual(self.referrer_partner.points, 150)
        self.assertEqual(self.referrer_partner.sign_up, 1)

    def test_refer_earn_generate_code(self):
        """Test /refer/earn generates referral code if not exist."""
        self.referrer_partner.referral_code = False
        self.mock_request.env.user = self.user
        
        self.ReferAndEarn.refer_earn()
        
        self.assertTrue(self.referrer_partner.referral_code)
        self.assertEqual(len(self.referrer_partner.referral_code), 7)
        self.mock_request.render.assert_called_with('refer_friend_and_earn.refer_earn_template', {
            'codes': self.referrer_partner.referral_code,
            'points': 100,
            'sign_up': 0
        })

    def test_refer_and_earn_popup(self):
        """Test refer_and_earn_popup sends email."""
        self.mock_request.env.user = self.user
        post_data = {'referral_code': 'ABCDEFG', 'email': 'friend@test.com'}
        
        self.ReferAndEarn.refer_and_earn_popup(**post_data)
        
        self.mock_request.render.assert_called_with('refer_friend_and_earn.website_success_page', {})

    def test_refer_earn_pricelist_points(self):
        """Test /shop/pricelist/points applies discount correctly."""
        self.mock_request.env.user = self.user
        kw = {'points': '100', 'r': '/shop/cart'}
        
        self.WebsiteSale.refer_earn(**kw)
        
        self.assertEqual(self.sale_order.discount_applied, 10.0)
        self.assertEqual(self.sale_order.points_applied, 100)
        self.assertEqual(len(self.sale_order.order_line), 2)
        discount_line = self.sale_order.order_line.filtered(lambda l: l.product_id == self.discount_product)
        self.assertEqual(discount_line.price_subtotal, -10.0)
        self.mock_request.redirect.assert_called_with('/shop/cart')

    def test_refer_earn_pricelist_points_lack(self):
        """Test lack of points returns specific template."""
        self.mock_request.env.user = self.user
        kw = {'points': '200', 'r': '/shop/cart'}
        
        self.WebsiteSale.refer_earn(**kw)
        
        self.mock_request.render.assert_called_with('refer_friend_and_earn.lack_of_points_template', {})

    @patch('odoo.addons.website_sale.controllers.main.WebsiteSale.cart_update_json')
    def test_cart_update_json(self, mock_super):
        """Test cart_update_json recalculates discount line."""
        mock_super.return_value = {}
        self.sale_order.discount_applied = 10.0
        self.sale_order.write({'order_line': [(0, 0, {
            'product_id': self.discount_product.id,
            'product_uom_qty': 1,
            'price_unit': -10.0
        })]})
        
        self.WebsiteSale.cart_update_json.original_routing['type'] = 'http'
            
        self.WebsiteSale.cart_update_json()
        
        discount_line = self.sale_order.order_line.filtered(lambda l: l.product_id == self.discount_product)
        self.assertEqual(discount_line.price_unit, -10.0)
        
    @patch('odoo.addons.website_sale.controllers.main.WebsiteSale.shop_payment_confirmation')
    def test_shop_payment_confirmation(self, mock_super):
        """Test shop_payment_confirmation deducts applied points."""
        mock_super.return_value = {}
        self.mock_request.session.get.return_value = self.sale_order.id
        self.mock_request.env.user = self.user
        self.sale_order.points_applied = 50
        
        self.WebsiteSale.shop_payment_confirmation()
        
        self.assertEqual(self.referrer_partner.points, 50)

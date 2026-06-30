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
from odoo.addons.refer_friend_and_earn.controllers.variants_discount import Cart


@tagged('post_install', '-at_install')
class TestVariantsDiscount(TransactionCase):
    """Test variants_discount controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Cart = Cart()
        
        cls.referrer_partner = cls.env['res.partner'].create({
            'name': 'Referrer Partner',
            'referral_code': 'ABCDEFG',
            'points': 100,
            'sign_up': 0
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
        
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100,
        })
        
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.referrer_partner.id,
            'discount_applied': 10.0,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100
                }),
                (0, 0, {
                    'product_id': cls.discount_product.id,
                    'product_uom_qty': 1,
                    'price_unit': -10.0
                })
            ]
        })

    def setUp(self):
        super().setUp()
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        self.mock_request.website = MagicMock()
        self.mock_request.website.sale_get_order.return_value = self.sale_order
        self.mock_request.render.return_value = werkzeug.wrappers.Response("Mocked Render")
        self.mock_request.redirect.return_value = werkzeug.wrappers.Response("Mocked Redirect")
        odoo.http._request_stack.push(self.mock_request)

    def tearDown(self):
        odoo.http._request_stack.pop()
        super().tearDown()

    @patch('odoo.addons.refer_friend_and_earn.controllers.variants_discount.WebsiteSaleProductConfiguratorController.cart_options_update_json', create=True)
    def test_cart_options_update_json(self, mock_super):
        """Test cart_options_update_json recalculates discount correctly."""
        mock_super.return_value = {}
        
        self.Cart.cart_options_update_json()
        
        discount_line = self.sale_order.order_line.filtered(lambda l: l.product_id == self.discount_product)
        self.assertEqual(discount_line.price_unit, -10.0)

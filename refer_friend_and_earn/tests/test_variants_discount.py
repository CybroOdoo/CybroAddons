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
from odoo.addons.website_sale.controllers.product_configurator import (
    WebsiteSaleProductConfiguratorController,
)
from odoo.addons.refer_friend_and_earn.controllers.variants_discount import Cart
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestVariantsDiscount(TransactionCase):
    """Test suite for variants discount controller Cart class."""

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

        cls.partner = cls.env['res.partner'].create({
            'name': 'Variant Cart User',
        })
        cls.regular_product = cls.env['product.product'].create({
            'name': 'Product With Variants Item',
            'list_price': 150.0,
            'type': 'consu',
        })

    def test_cart_options_update_json(self):
        """Test cart_options_update_json recalculates discount price for cart items with variants."""
        controller = Cart()
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'discount_applied': 10.0,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.regular_product.id,
            'product_uom_qty': 2,
            'price_unit': 150.0,
        })
        discount_line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.discount_product.id,
            'product_uom_qty': 1,
            'price_unit': -15.0,
        })

        mock_req = MagicMock()
        with patch('odoo.addons.refer_friend_and_earn.controllers.variants_discount.request', new=mock_req):
            mock_req.env = self.env
            mock_req.cart = order

            with patch.object(WebsiteSaleProductConfiguratorController, 'cart_options_update_json', create=True, return_value={'success': True}):
                res = controller.cart_options_update_json()
                discount_line.invalidate_recordset()
                # Total subtotal is regular line (300) + discount line (-15) = 285
                # original_total_price = 285 - (-15) = 300
                # discount_amount = 300 * (10 / 100) = 30.0 -> order_line_discount_price = -30.0
                self.assertEqual(discount_line.price_unit, -30.0)
                self.assertEqual(res, {'success': True})

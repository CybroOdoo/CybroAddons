# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
import logging
import json

from odoo.tests import HttpCase, tagged
logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestEcommerceQuickView(HttpCase):
    """Exercise the public quick-view endpoint and its visibility rules."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.published_product = cls.env['product.template'].create({
            'name': 'Quick View Test Product',
            'list_price': 42.50,
            'website_published': True,
        })
        cls.unpublished_product = cls.env['product.template'].create({
            'name': 'Hidden Quick View Test Product',
            'website_published': False,
        })

    def _quick_view(self, product_id):
        response = self.url_open(
            '/c_quick_view/get_quick_view_html',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {'product_id': product_id},
                'id': 1,
            }),
            headers={'Content-Type': 'application/json'},
        )
        return response.json().get('result')
    def test_published_product_returns_quick_view_modal(self):
        html = self._quick_view(self.published_product.id)

        self.assertIn('c_product_quick_view_modal', html)
        self.assertIn('Quick View Test Product', html)
        self.assertIn('product_template_id', html)
        self.assertIn(str(self.published_product.id), html)
        self.assertIn('View Product Details', html)
        logger.info('PASSED : test_published_product_returns_quick_view_modal')


    def test_invalid_product_id_returns_empty_response(self):
        for product_id in (None, 0, 'invalid', 99999999):
            with self.subTest(product_id=product_id):
                self.assertFalse(self._quick_view(product_id))
        logger.info('PASSED : test_invalid_product_id_returns_empty_response')

    def test_unpublished_product_is_not_exposed(self):
        self.assertFalse(self._quick_view(self.unpublished_product.id))
        logger.info('PASSED : test_unpublished_product_is_not_exposed')

    def test_shop_product_tile_has_quick_view_action(self):
        response = self.url_open('/shop')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'c-product-quick-view-action', response.content)
        self.assertIn(
            ('data-product-id="%s"' % self.published_product.id).encode(),
            response.content,
        )
        logger.info('PASSED : test_shop_product_tile_has_quick_view_action')

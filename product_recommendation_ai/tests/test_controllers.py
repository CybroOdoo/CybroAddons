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

from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestProductRecommendationControllers(HttpCase):
    """Test suite for recommendation HTTP and JSON-RPC controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_category = cls.env['product.public.category'].create({
            'name': 'Controller Test Category',
        })
        cls.test_product = cls.env['product.template'].create({
            'name': 'Category Test Product',
            'website_published': True,
            'public_categ_ids': [(4, cls.test_category.id)],
        })
        cls.test_user = cls.env['res.users'].create({
            'name': 'Controller Test Customer',
            'login': 'controller_test_user',
            'password': 'password123',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_session_recommendations_get(self):
        """Test getting session recommendations via JSON-RPC."""
        self.authenticate(self.test_user.login, 'password123')

        # Initially, recommendation list should be empty
        initial_reco = self.make_jsonrpc_request('/recommendation/session/get')
        self.assertEqual(initial_reco, [])

        # When user has recommendations data computed
        test_payload = [
            {
                'product_id': 101,
                'name': 'Recommended Test Phone',
                'display_text': 'Recommended Test Phone. High Tech.',
                'list_price': 599.0,
                'currency': '$',
                'image': '/web/image/product.template/101/image_1920',
            }
        ]
        self.test_user.sudo().recommended_products_data = test_payload

        # Verify recommendations are returned
        saved_reco = self.make_jsonrpc_request('/recommendation/session/get')
        self.assertEqual(saved_reco, test_payload)

    def test_shop_pagination_and_category_routes(self):
        """Test that shop pagination and category routes are preserved by @http.route()."""
        # Pagination route
        res_page = self.url_open('/shop/page/1')
        self.assertEqual(res_page.status_code, 200)

        # Category route with slug
        category_slug = self.env['ir.http']._slug(self.test_category)
        res_cat = self.url_open(f'/shop/category/{category_slug}')
        self.assertEqual(res_cat.status_code, 200)

        # Category pagination route
        res_cat_page = self.url_open(f'/shop/category/{category_slug}/page/1')
        self.assertEqual(res_cat_page.status_code, 200)

    def test_shop_route_public_user(self):
        """Test visiting /shop as public user does not trigger run_recommendation_async."""
        target = self.env.registry['res.users']
        with patch.object(target, 'run_recommendation_async') as mock_run_async:
            response = self.url_open('/shop')
            self.assertEqual(response.status_code, 200)
            mock_run_async.assert_not_called()

    def test_shop_route_logged_in_user(self):
        """Test visiting /shop as logged-in user triggers run_recommendation_async."""
        self.authenticate(self.test_user.login, 'password123')
        target = self.env.registry['res.users']
        with patch.object(target, 'run_recommendation_async') as mock_run_async:
            response = self.url_open('/shop')
            self.assertEqual(response.status_code, 200)
            mock_run_async.assert_called_once()

    def test_shop_route_handles_async_exception(self):
        """Test /shop handles exceptions during run_recommendation_async without crashing."""
        self.authenticate(self.test_user.login, 'password123')
        target = self.env.registry['res.users']
        with patch.object(target, 'run_recommendation_async', side_effect=Exception("Async failure")):
            response = self.url_open('/shop')
            self.assertEqual(response.status_code, 200)

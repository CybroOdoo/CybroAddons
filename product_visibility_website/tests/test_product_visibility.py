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
from odoo import http
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestProductVisibility(HttpCase):
    """Test suite for website product and category visibility."""

    def setUp(self):
        super().setUp()
        if not hasattr(http, 'GEOIP_EMPTY_COUNTRY'):
            class MockGeoIP:
                def __getattr__(self, name):
                    return None

            http.GEOIP_EMPTY_COUNTRY = MockGeoIP()
            http.GEOIP_EMPTY_CITY = MockGeoIP()

    def test_search_filtering_guest(self):
        """Test that public users only see products in allowed categories."""
        category_allowed = self.env['product.public.category'].create({
            'name': 'Allowed Category',
        })
        category_restricted = self.env['product.public.category'].create({
            'name': 'Restricted Category',
        })

        self.env['product.template'].create({
            'name': 'Visible Search Product',
            'public_categ_ids': [(4, category_allowed.id)],
            'is_published': True,
            'list_price': 100.0,
        })
        self.env['product.template'].create({
            'name': 'Hidden Search Product',
            'public_categ_ids': [(4, category_restricted.id)],
            'is_published': True,
            'list_price': 200.0,
        })

        # Configure Guest Visibility (Category Wise)
        self.env['ir.config_parameter'].sudo().set_bool(
            'is_product_visibility_guest_user', True
        )
        self.env['ir.config_parameter'].sudo().set_str(
            'filter_mode', 'categ_only'
        )
        self.env['ir.config_parameter'].sudo().set_str(
            'website_product_visibility.available_cat_for_guest_ids',
            str([category_allowed.id]),
        )

        response = self.url_open('/shop?search=Search Product')
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            'Visible Search Product',
            response.text,
            "Allowed product should be visible in search.",
        )
        self.assertNotIn(
            'Hidden Search Product',
            response.text,
            "Restricted product should be hidden from search.",
        )

    def test_search_filtering_guest_product_wise(self):
        """Guest product mode only exposes explicitly selected products."""
        product_allowed = self.env['product.template'].create({
            'name': 'Guest Product Wise Allowed',
            'is_published': True,
        })
        self.env['product.template'].create({
            'name': 'Guest Product Wise Hidden',
            'is_published': True,
        })

        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('is_product_visibility_guest_user', True)
        params.set_str('filter_mode', 'product_only')
        params.set_str(
            'website_product_visibility.available_products_for_guest_ids',
            str([product_allowed.id]),
        )

        response = self.url_open('/shop?search=Guest Product Wise')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Guest Product Wise Allowed', response.text)
        self.assertNotIn('Guest Product Wise Hidden', response.text)

    def test_partner_visibility_category_tree(self):
        """Partner category mode includes products in descendant categories."""
        parent_category = self.env['product.public.category'].create({
            'name': 'Partner Allowed Parent',
        })
        child_category = self.env['product.public.category'].create({
            'name': 'Partner Allowed Child',
            'parent_id': parent_category.id,
        })
        outside_category = self.env['product.public.category'].create({
            'name': 'Partner Outside Category',
        })
        self.env['product.template'].create({
            'name': 'Partner Child Category Product',
            'public_categ_ids': [(4, child_category.id)],
            'is_published': True,
        })
        self.env['product.template'].create({
            'name': 'Partner Outside Category Product',
            'public_categ_ids': [(4, outside_category.id)],
            'is_published': True,
        })

        partner = self.env['res.partner'].create({
            'name': 'Category Restricted Partner',
            'filter_mode': 'categ_only',
            'website_available_cat_ids': [(4, parent_category.id)],
        })
        self.env['res.users'].create({
            'name': 'Category Restricted User',
            'login': 'category_restricted_user_login',
            'password': 'password123',
            'partner_id': partner.id,
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        self.authenticate('category_restricted_user_login', 'password123')
        response = self.url_open('/shop?search=Category Product')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Partner Child Category Product', response.text)
        self.assertNotIn('Partner Outside Category Product', response.text)

    def test_partner_visibility_product_wise(self):
        """Test that logged-in partner only sees whitelisted products."""
        product_allowed = self.env['product.template'].create({
            'name': 'Partner Allowed Product',
            'is_published': True,
        })
        self.env['product.template'].create({
            'name': 'Partner Denied Product',
            'is_published': True,
        })

        partner = self.env['res.partner'].create({
            'name': 'Restricted Partner',
            'filter_mode': 'product_only',
            'website_available_product_ids': [(4, product_allowed.id)],
        })
        self.env['res.users'].create({
            'name': 'Restricted User',
            'login': 'restricted_user_login',
            'password': 'password123',
            'partner_id': partner.id,
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        self.authenticate('restricted_user_login', 'password123')
        response = self.url_open('/shop?search=Partner')

        self.assertIn('Partner Allowed Product', response.text)
        self.assertNotIn('Partner Denied Product', response.text)

    def test_partner_visibility_categories_sidebar(self):
        """Test that only allowed categories appear in sidebar for partner."""
        furniture_parent = self.env['product.public.category'].create({
            'name': 'Furniture Parent',
        })
        category_desks = self.env['product.public.category'].create({
            'name': 'Allowed Desks',
            'parent_id': furniture_parent.id,
        })
        category_bins = self.env['product.public.category'].create({
            'name': 'Allowed Bins',
        })
        category_chairs = self.env['product.public.category'].create({
            'name': 'Forbidden Chairs',
            'parent_id': furniture_parent.id,
        })
        category_clothing = self.env['product.public.category'].create({
            'name': 'Forbidden Clothing',
        })

        self.env['product.template'].create({
            'name': 'Desk Product',
            'public_categ_ids': [(4, category_desks.id)],
            'is_published': True,
        })
        self.env['product.template'].create({
            'name': 'Bin Product',
            'public_categ_ids': [(4, category_bins.id)],
            'is_published': True,
        })
        self.env['product.template'].create({
            'name': 'Chair Product',
            'public_categ_ids': [(4, category_chairs.id)],
            'is_published': True,
        })
        self.env['product.template'].create({
            'name': 'Shirt Product',
            'public_categ_ids': [(4, category_clothing.id)],
            'is_published': True,
        })

        partner = self.env['res.partner'].create({
            'name': 'Category Filtered Partner',
            'filter_mode': 'categ_only',
            'website_available_cat_ids': [
                (4, category_desks.id),
                (4, category_bins.id),
            ],
        })
        self.env['res.users'].create({
            'name': 'Category Filtered User',
            'login': 'category_filtered_user_login',
            'password': 'password123',
            'partner_id': partner.id,
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        self.authenticate('category_filtered_user_login', 'password123')
        response = self.url_open('/shop')
        self.assertEqual(response.status_code, 200)

        self.assertIn('Allowed Desks', response.text)
        self.assertIn('Allowed Bins', response.text)
        self.assertNotIn('Forbidden Chairs', response.text)
        self.assertNotIn('Forbidden Clothing', response.text)

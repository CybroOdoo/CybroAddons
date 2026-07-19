# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestProductVisibility(HttpCase):
    
    def setUp(self):
        super(TestProductVisibility, self).setUp()
        # Bypass Odoo 19 GeoIP bug (GEOIP_EMPTY_COUNTRY NameError)
        from odoo import http
        if not hasattr(http, 'GEOIP_EMPTY_COUNTRY'):
            class MockGeoIP:
                def __getattr__(self, name): return None
            http.GEOIP_EMPTY_COUNTRY = MockGeoIP()
            http.GEOIP_EMPTY_CITY = MockGeoIP()

    def test_search_filtering_guest(self):
        """Test that public users only see products in allowed categories."""
        # Setup test data
        category_allowed = self.env['product.public.category'].create({'name': 'Allowed Category'})
        category_restricted = self.env['product.public.category'].create({'name': 'Restricted Category'})
        
        product_visible = self.env['product.template'].create({
            'name': 'Visible Search Product',
            'public_categ_ids': [(4, category_allowed.id)],
            'is_published': True,
            'list_price': 100.0,
        })
        product_hidden = self.env['product.template'].create({
            'name': 'Hidden Search Product',
            'public_categ_ids': [(4, category_restricted.id)],
            'is_published': True,
            'list_price': 200.0,
        })

        # Configure Guest Visibility (Category Wise)
        self.env['ir.config_parameter'].sudo().set_param('is_product_visibility_guest_user', True)
        self.env['ir.config_parameter'].sudo().set_param('filter_mode', 'categ_only')
        self.env['ir.config_parameter'].sudo().set_param('website_product_visibility.available_cat_for_guest_ids', [category_allowed.id])

        # Step 1: Search as Public User
        response = self.url_open('/shop?search=Search Product')
        self.assertEqual(response.status_code, 200)
        
        # Verify visibility
        self.assertIn('Visible Search Product', response.text, "Allowed product should be visible in search")
        self.assertNotIn('Hidden Search Product', response.text, "Restricted product should be hidden from search")

    def test_partner_visibility_product_wise(self):
        """Test that a logged-in partner only sees specific whitelisted products."""
        # Setup test data
        product_allowed = self.env['product.template'].create({
            'name': 'Partner Allowed Product',
            'is_published': True,
        })
        product_denied = self.env['product.template'].create({
            'name': 'Partner Denied Product',
            'is_published': True,
        })

        # Create a portal user and link to partner
        partner = self.env['res.partner'].create({
            'name': 'Restricted Partner',
            'filter_mode': 'product_only',
            'website_available_product_ids': [(4, product_allowed.id)]
        })
        user = self.env['res.users'].create({
            'name': 'Restricted User',
            'login': 'restricted_user_login',
            'password': 'password123',
            'partner_id': partner.id,
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])]
        })

        # Log in and check visibility
        self.authenticate('restricted_user_login', 'password123')
        response = self.url_open('/shop?search=Partner')
        
        self.assertIn('Partner Allowed Product', response.text)
        self.assertNotIn('Partner Denied Product', response.text)

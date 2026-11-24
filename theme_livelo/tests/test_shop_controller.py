# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from werkzeug.datastructures import MultiDict
from odoo.tests import common, tagged
from odoo.addons.http_routing.tests.common import MockRequest
from odoo.addons.theme_livelo.controller.shop_product import CustomWebsiteSale, _parse_price_range


@tagged('post_install', '-at_install')
class TestPriceRangeParser(common.BaseCase):
    """Unit tests for _parse_price_range helper function."""

    def test_parse_price_range_none_and_empty(self):
        """Test parsing empty or None price range strings."""
        self.assertEqual(_parse_price_range(None), (None, None))
        self.assertEqual(_parse_price_range(""), (None, None))
        self.assertEqual(_parse_price_range("   "), (None, None))

    def test_parse_price_range_hyphenated(self):
        """Test parsing standard hyphenated price ranges."""
        self.assertEqual(_parse_price_range("0-5000"), (0.0, 5000.0))
        self.assertEqual(_parse_price_range("5000-10000"), (5000.0, 10000.0))
        self.assertEqual(_parse_price_range("10000-50000"), (10000.0, 50000.0))
        self.assertEqual(_parse_price_range(" 2500 - 7500 "), (2500.0, 7500.0))

    def test_parse_price_range_plus_and_open_ended(self):
        """Test parsing plus and open-ended price range strings."""
        self.assertEqual(_parse_price_range("50000+"), (50000.0, None))
        self.assertEqual(_parse_price_range("50000-plus"), (50000.0, None))
        self.assertEqual(_parse_price_range("50000plus"), (50000.0, None))
        self.assertEqual(_parse_price_range("50000 "), (50000.0, None))
        self.assertEqual(_parse_price_range("50000"), (50000.0, None))
        self.assertEqual(_parse_price_range(" 100000+ "), (100000.0, None))

    def test_parse_price_range_invalid(self):
        """Test parsing invalid price range strings."""
        self.assertEqual(_parse_price_range("invalid"), (None, None))
        self.assertEqual(_parse_price_range("abc-def"), (None, None))
        self.assertEqual(_parse_price_range("5000-abc"), (None, None))
        self.assertEqual(_parse_price_range("+"), (None, None))
        self.assertEqual(_parse_price_range("-plus"), (None, None))


@tagged('post_install', '-at_install')
class TestCustomWebsiteSaleUnit(common.HttpCase):
    """Unit tests for CustomWebsiteSale controller methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = CustomWebsiteSale()
        cls.website = cls.env['website'].get_current_website()

        # Load theme templates onto the current website
        theme_module = cls.env['ir.module.module'].search([('name', '=', 'theme_livelo')])
        if theme_module:
            theme_module.with_context(load_all_views=True)._theme_load(cls.website)

        # Retrieve a property created by theme_livelo data
        cls.property = cls.env.ref('theme_livelo.product_property_1', raise_if_not_found=False)
        if not cls.property:
            cls.property = cls.env['product.template'].create({
                'name': 'Test Livelo Villa',
                'is_property': True,
                'list_price': 7250.0,
                'listing_type': 'sale',
                'property_type': 'house',
                'location': 'California',
                'bed': 3,
                'bath': 2,
                'website_published': True,
            })
            cls.env['ir.model.data'].create({
                'name': 'product_property_test_unit',
                'module': 'theme_livelo',
                'model': 'product.template',
                'res_id': cls.property.id,
            })

    def test_get_search_order(self):
        """Test custom sorting mappings for properties."""
        with MockRequest(self.env, website=self.website):
            self.assertEqual(
                self.controller._get_search_order({'sort': 'newest'}),
                'create_date desc, id desc'
            )
            self.assertEqual(
                self.controller._get_search_order({'sort': 'price_asc'}),
                'list_price asc, id desc'
            )
            self.assertEqual(
                self.controller._get_search_order({'sort': 'price_desc'}),
                'list_price desc, id desc'
            )
            default_order = self.controller._get_search_order({})
            self.assertTrue(default_order)

    def test_get_shop_domain_filters(self):
        """Test domain building in _get_shop_domain with various parameter combinations."""
        with MockRequest(self.env, website=self.website) as req:
            req.httprequest.args = MultiDict()

            # 1. Base domain checks (is_property=True and theme_livelo product ids)
            domain = self.controller._get_shop_domain('', None, {})
            domain_repr = str(domain)
            self.assertIn("'is_property', '=', True", domain_repr)

            # 2. Location filter
            req.params = {'location': 'Chicago'}
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('location', 'ilike', 'Chicago')", str(domain))

            # 3. Listing filter
            req.params = {'listing': 'rent'}
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('listing_type', '=', 'rent')", str(domain))

            # 4. Property type filter
            req.params = {'type': 'apartment'}
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('property_type', '=', 'apartment')", str(domain))

            # 5. Beds filter exact and >= 4
            req.params = {'beds': '3'}
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('bed', '=', 3)", str(domain))

            req.params = {'beds': '4'}
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('bed', '>=', 4)", str(domain))

            # 6. Baths filter exact and >= 3
            req.params = {'baths': '2'}
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('bath', '=', 2)", str(domain))

            req.params = {'baths': '3'}
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('bath', '>=', 3)", str(domain))

            # 7. Price range filter
            req.params = {'price_range': '2000-8000'}
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('list_price', '>=', 2000.0)", str(domain))
            self.assertIn("('list_price', '<=', 8000.0)", str(domain))

            req.params = {'price_range': '50000+'}
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('list_price', '>=', 50000.0)", str(domain))

            # 8. Amenities filter via httprequest.args
            req.params = {}
            req.httprequest.args = MultiDict({'amenities': '1'})
            domain = self.controller._get_shop_domain('', None, {})
            self.assertIn("('amenity_ids', 'in', 1)", str(domain))

    def test_property_contact_lead_creation_direct(self):
        """Test direct invocation of property_contact controller method."""
        with MockRequest(self.env, website=self.website):
            response = self.controller.property_contact(
                product_id=str(self.property.id),
                contact_name='Direct Test Buyer',
                mobile='+1987654321',
                email='direct_buyer@example.com',
                message='I would like to schedule an inspection.'
            )
            self.assertTrue(response)

            lead = self.env['crm.lead'].search([('email_from', '=', 'direct_buyer@example.com')], limit=1)
            self.assertTrue(lead, "CRM Lead should have been created")
            self.assertIn(self.property.name, lead.name)
            self.assertEqual(lead.contact_name, 'Direct Test Buyer')
            self.assertEqual(lead.phone, '+1987654321')
            self.assertIn('I would like to schedule an inspection.', lead.description)
            if self.property.salesperson_id:
                self.assertEqual(lead.user_id, self.property.salesperson_id)

    def test_property_contact_fallback_name(self):
        """Test property_contact without product_id creates a lead named 'Property Lead'."""
        with MockRequest(self.env, website=self.website):
            self.controller.property_contact(
                contact_name='General Inquirer',
                mobile='+1112223333',
                email='general_inquiry@example.com',
                message='Looking for general property information.'
            )
            lead = self.env['crm.lead'].search([('email_from', '=', 'general_inquiry@example.com')], limit=1)
            self.assertTrue(lead)
            self.assertEqual(lead.name, 'Property Lead')


@tagged('post_install', '-at_install')
class TestShopControllerHttp(common.HttpCase):
    """HTTP integration tests for theme_livelo shop, product details, contact form, and static pages."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()

        # Load theme templates onto the current website so QWeb templates exist
        theme_module = cls.env['ir.module.module'].search([('name', '=', 'theme_livelo')])
        if theme_module:
            theme_module.with_context(load_all_views=True)._theme_load(cls.website)

        # Ensure we have a published property
        cls.property = cls.env.ref('theme_livelo.product_property_1', raise_if_not_found=False)
        if cls.property:
            cls.property.write({
                'website_published': True,
                'is_published': True,
            })

    def test_01_shop_page_http_200(self):
        """Test GET /shop loads successfully with HTTP 200."""
        res = self.url_open('/shop')
        self.assertEqual(res.status_code, 200, "Shop page should return HTTP 200")
        self.assertIn('container-featured-properties', res.text)

    def test_02_shop_page_filters_query_params(self):
        """Test GET /shop with various filter query params."""
        filter_urls = [
            '/shop?listing=sale',
            '/shop?listing=rent',
            '/shop?type=house',
            '/shop?type=apartment',
            '/shop?location=California',
            '/shop?beds=3',
            '/shop?beds=4',
            '/shop?baths=2',
            '/shop?baths=3',
            '/shop?price_range=0-5000',
            '/shop?price_range=50000%2B',
            '/shop?sort=newest',
            '/shop?sort=price_asc',
            '/shop?sort=price_desc',
        ]
        for url in filter_urls:
            res = self.url_open(url)
            self.assertEqual(
                res.status_code, 200,
                f"Shop page filter URL '{url}' should return HTTP 200"
            )

    def test_03_property_detail_page_http_200(self):
        """Test GET property detail page returns HTTP 200 and property information."""
        if not self.property:
            self.skipTest("No theme_livelo property found")

        url = f"/shop/{self.property.id}"
        res = self.url_open(url)
        self.assertEqual(res.status_code, 200, "Property detail page should return HTTP 200")
        self.assertIn(self.property.name, res.text)
        self.assertIn('/property/contact', res.text)

    def test_04_property_contact_post_creates_lead(self):
        """Test submitting the property contact form via POST creates a crm.lead."""
        if not self.property:
            self.skipTest("No theme_livelo property found")

        # 1. Open the property detail page to obtain a session and CSRF token
        product_res = self.url_open(f"/shop/{self.property.id}")
        self.assertEqual(product_res.status_code, 200)

        csrf_anchor = '<input type="hidden" name="csrf_token" value="'
        csrf_token = product_res.text.partition(csrf_anchor)[2].partition('"')[0]
        self.assertTrue(csrf_token, "CSRF token should be extracted from property page")

        contact_payload = {
            'csrf_token': csrf_token,
            'product_id': str(self.property.id),
            'contact_name': 'Jane Contact Test',
            'mobile': '+15551234567',
            'email': 'jane.contact@example.com',
            'message': 'Hello, I want to book a visit for this property.',
        }

        # 2. Submit the form
        post_res = self.url_open('/property/contact', data=contact_payload)
        self.assertEqual(post_res.status_code, 200, "Contact form POST should return HTTP 200")
        self.assertIn('Thank You', post_res.text)

        # 3. Verify lead in CRM
        lead = self.env['crm.lead'].sudo().search([
            ('email_from', '=', 'jane.contact@example.com')
        ], limit=1)
        self.assertTrue(lead, "CRM Lead should be created after submitting contact form")
        self.assertEqual(lead.contact_name, 'Jane Contact Test')
        self.assertEqual(lead.phone, '+15551234567')
        self.assertIn(self.property.name, lead.name)
        self.assertIn('Hello, I want to book a visit for this property.', lead.description)

    def test_05_static_routes_http_200(self):
        """Test static informational pages defined in theme_livelo."""
        static_pages = ['/service', '/location', '/pricing', '/aboutus']
        for page in static_pages:
            res = self.url_open(page)
            self.assertEqual(
                res.status_code, 200,
                f"Page '{page}' should return HTTP 200"
            )

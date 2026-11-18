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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPropellePages(HttpCase):
    """Test that every page and header template of the theme renders."""

    @classmethod
    def setUpClass(cls):
        """Apply the theme to the website."""
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        theme = cls.env['ir.module.module'].search(
            [('name', '=', 'theme_propelle')], limit=1)
        theme._theme_load(cls.website)
        city = cls.env['propelle.city'].search([], limit=1)
        cls.env['propelle.property'].create({
            'name': 'Test Villa',
            'listing_type': 'sale',
            'property_type': 'villa',
            'city_id': city.id,
            'price': 1000000,
            'is_published': True,
        })
        cls.env['propelle.project'].create({
            'name': 'Test Residences',
            'location': 'Malibu, CA',
            'is_published': True,
        })

    def test_pages_render(self):
        """Each page answers and carries the theme markup."""
        for url, marker in (
            ('/', 'pp-header'),
            ('/about', 'pp-header'),
            ('/sell', 'pp-header'),
            ('/contactus', 'pp-header'),
            ('/buy', 'pp-listings'),
            ('/rent', 'pp-listings'),
            ('/projects', 'pp-dev'),
            ('/booking', 'booking-form'),
        ):
            with self.subTest(url=url):
                response = self.url_open(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn(marker, response.text)

    def test_listing_filters_in_markup(self):
        """The cards carry the data the filters read."""
        response = self.url_open('/buy')
        self.assertIn('data-price=', response.text)
        self.assertIn('data-location=', response.text)

    def test_listings_are_paged_and_filtered(self):
        """The server pages the listings and applies the filter bar."""
        city = self.env['propelle.city'].search([], limit=1)
        self.env['propelle.property'].create([{
            'name': 'Paged Flat {}'.format(index),
            'listing_type': 'sale',
            'property_type': 'apartment',
            'city_id': city.id,
            'price': 100000 + index * 1000,
            'is_published': True,
        } for index in range(13)])
        marker = '<article class="pp-pcard'
        first = self.url_open('/buy').text
        second = self.url_open('/buy/page/2').text
        self.assertEqual(first.count(marker), 12)
        self.assertGreaterEqual(second.count(marker), 2)
        self.assertIn('/buy/page/2', first)
        villas = self.url_open('/buy?type=villa').text
        self.assertIn('Test Villa', villas)
        self.assertNotIn('Paged Flat', villas)
        cheap = self.url_open('/buy?max=105000&sort=price-desc').text
        self.assertEqual(cheap.count(marker), 6)
        self.assertLess(
            cheap.index('Paged Flat 5'), cheap.index('Paged Flat 0'))
        self.assertEqual(self.url_open('/buy/page/99').status_code, 200)

    def test_data_route(self):
        """The data route gives the cities, types and budgets."""
        data = self.make_jsonrpc_request('/propelle/data', {})
        self.assertTrue(data['cities'])
        self.assertTrue(data['types'])
        self.assertTrue(data['budgets']['sale'])
        self.assertTrue(data['budgets']['rent'])

    def test_header_templates(self):
        """Another header template renders, and Default brings the design."""
        view_model = self.env['ir.ui.view']
        for key in ('website.template_header_hamburger',
                    'website.template_header_default'):
            view = view_model.search([('key', '=', key)], limit=1)
            if not view:
                continue
            with self.subTest(key=key):
                self.website.with_context(website_id=self.website.id)
                response = self.url_open('/')
                self.assertEqual(response.status_code, 200)

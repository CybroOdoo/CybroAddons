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

import json
from unittest.mock import MagicMock, patch

from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger

from odoo.addons.theme_petzen.controllers.theme_petzen import PetzenServices

CONTROLLER = 'odoo.addons.theme_petzen.controllers.theme_petzen'
USER_LOGIN = 'petzen_test_user'
USER_PASSWORD = 'petzen_test_user_pw'


@tagged('post_install', '-at_install', 'theme_petzen')
class TestPetzenControllers(HttpCase):
    """Test the pages, forms and JSON routes of the Petzen theme."""

    @classmethod
    def setUpClass(cls):
        """Apply the theme, create a published product and a customer user."""
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()
        # the theme templates are only available on a website once the theme is applied
        theme = cls.env['ir.module.module'].search([('name', '=', 'theme_petzen')])
        theme._theme_remove(cls.website)
        cls.website.theme_id = theme
        theme._theme_load(cls.website)
        cls.product =cls.env['product.template'].create({
            'name': 'Petzen Test Chew Toy',
            'list_price': 20.0,
            'categ_id': cls.env.ref('theme_petzen.product_category_dog').id,
            'is_published': True,
            'sale_ok': True,
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Petzen Customer',
            'login': USER_LOGIN,
            'password': USER_PASSWORD,
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def _rpc(self, route, **params):
        """Call a JSON route and return its result."""
        response = self.url_open(
            route,
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': params}),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.status_code, 200, route)
        payload = response.json()
        self.assertNotIn('error', payload, payload.get('error'))
        return payload['result']

    # ── Pages ────────────────────────────────────────────────────────────────

    def test_pages(self):
        """The theme pages are rendered."""
        for url in ('/services', '/about', '/reviews', '/contact'):
            with self.subTest(url=url):
                self.assertEqual(self.url_open(url).status_code, 200)

    # ── Reviews ──────────────────────────────────────────────────────────────

    def test_get_reviews_data(self):
        """Only approved reviews are returned, with initials and stars."""
        Review = self.env['petzen.review']
        Review.create({'name': 'Ann Lee', 'email': 'a@example.com', 'review': 'Nice', 'rating': 4,
                       'state': 'approved'})
        Review.create({'name': 'Bob', 'email': 'b@example.com', 'review': 'Perfect', 'rating': 5,
                       'state': 'approved'})
        Review.create({'name': 'Hidden', 'email': 'h@example.com', 'review': 'Pending'})
        result = self._rpc('/theme_petzen/get_reviews_data')
        by_name = {r['name']: r for r in result['reviews']}
        self.assertEqual(set(by_name), {'Ann Lee', 'Bob'})
        self.assertEqual(by_name['Ann Lee']['initials'], 'AL')
        self.assertEqual(by_name['Ann Lee']['stars'], '★' * 4)
        self.assertEqual(by_name['Ann Lee']['empty_stars'], '★')
        self.assertEqual(by_name['Bob']['empty_stars'], '')
        limited = self._rpc('/theme_petzen/get_reviews_data', limit=1)
        self.assertEqual(len(limited['reviews']), 1)

    def test_submit_review(self):
        """A valid review is stored as pending; invalid ones are refused."""
        route = '/reviews/submit'
        self.assertFalse(self._rpc(route, name='', email='', review='')['success'])
        result = self._rpc(route, name='Cara', email='not-an-email', review='Good')
        self.assertFalse(result['success'])
        self.assertIn('valid email', result['error'])
        self.assertTrue(self._rpc(route, name='Cara', email='cara@example.com', review='Good',
                                  rating=9)['success'])
        review = self.env['petzen.review'].search([('email', '=', 'cara@example.com')])
        self.assertEqual(review.state, 'pending')
        self.assertEqual(review.rating, 5)
        self.assertTrue(self._rpc(route, name='Dan', email='dan@example.com', review='Ok',
                                  rating='abc')['success'])
        self.assertEqual(self.env['petzen.review'].search([('email', '=', 'dan@example.com')]).rating, 5)
        self.assertTrue(self._rpc(route, name='Eve', email='eve@example.com', review='Bad',
                                  rating=-3)['success'])
        self.assertEqual(self.env['petzen.review'].search([('email', '=', 'eve@example.com')]).rating, 1)

    @mute_logger(CONTROLLER)
    def test_submit_review_failure(self):
        """A failure while saving the review is reported to the visitor."""
        with patch('odoo.addons.theme_petzen.models.petzen_review.PetzenReview.create',
                   side_effect=ValueError('boom')):
            result = self._rpc('/reviews/submit', name='Fay', email='fay@example.com', review='Hi')
        self.assertFalse(result['success'])
        self.assertIn('Something went wrong', result['error'])

    # ── CRM leads ────────────────────────────────────────────────────────────

    def test_submit_contact(self):
        """The contact form creates a CRM lead."""
        route = '/contact/submit'
        self.assertFalse(self._rpc(route, first_name='', email='', message='')['success'])
        self.assertFalse(self._rpc(route, first_name='Gus', email='bad', message='Hello')['success'])
        self.assertTrue(self._rpc(route, first_name='Gus', last_name='Hill', email='gus@example.com',
                                  phone='123', department='Adoption', message='Hello')['success'])
        lead = self.env['crm.lead'].search([('email_from', '=', 'gus@example.com')])
        self.assertEqual(lead.name, '[Petzen] Adoption')
        self.assertEqual(lead.contact_name, 'Gus Hill')
        self.assertIn('Topic: Adoption', lead.description)
        self.assertTrue(self._rpc(route, first_name='Hal', email='hal@example.com',
                                  message='No topic')['success'])
        lead = self.env['crm.lead'].search([('email_from', '=', 'hal@example.com')])
        self.assertEqual(lead.name, '[Petzen] General Inquiry')
        self.assertEqual(lead.contact_name, 'Hal')
        self.assertFalse(lead.phone)

    def test_book_service(self):
        """The booking form creates a CRM lead."""
        route = '/services/book'
        self.assertFalse(self._rpc(route)['success'])
        full = dict(pet_name='Rex', pet_type='Dog', service='Grooming', owner_name='Ivy',
                    email='ivy@example.com', phone='555', date='2026-12-01', notes='Be gentle')
        self.assertFalse(self._rpc(route, **dict(full, email='nope'))['success'])
        self.assertTrue(self._rpc(route, **full)['success'])
        lead = self.env['crm.lead'].search([('email_from', '=', 'ivy@example.com')])
        self.assertEqual(lead.name, '[Petzen Booking] Grooming for Rex')
        self.assertIn('Notes:\nBe gentle', lead.description)
        self.assertTrue(self._rpc(route, **dict(full, email='jo@example.com', notes='', phone=''))['success'])
        lead = self.env['crm.lead'].search([('email_from', '=', 'jo@example.com')])
        self.assertNotIn('Notes:', lead.description)

    def test_newsletter(self):
        """The footer form creates a CRM lead."""
        self.assertFalse(self._rpc('/petzen/newsletter')['success'])
        self.assertFalse(self._rpc('/petzen/newsletter', email='bad')['success'])
        self.assertTrue(self._rpc('/petzen/newsletter', email='news@example.com')['success'])
        lead = self.env['crm.lead'].search([('email_from', '=', 'news@example.com')])
        self.assertEqual(lead.name, '[Petzen] Newsletter subscription')

    @mute_logger(CONTROLLER)
    def test_create_lead_failure(self):
        """A failure while creating the lead is reported to the visitor."""
        with patch('odoo.addons.crm.models.crm_lead.Lead.create', side_effect=ValueError('boom')):
            result = self._rpc('/petzen/newsletter', email='fail@example.com')
        self.assertFalse(result['success'])
        self.assertIn('Something went wrong', result['error'])

    # ── Live blocks ──────────────────────────────────────────────────────────

    def test_home_categories(self):
        """The category tiles are rendered for the home snippet."""
        html = self._rpc('/petzen/home/categories')['html']
        self.assertIn('cat-bento', html)
        self.assertIn('Dog', html)

    def test_home_products(self):
        """The product tabs and carousel are rendered for the home snippet."""
        html = self._rpc('/petzen/home/products')['html']
        self.assertIn('tab-pill', html)
        self.assertIn('Petzen Test Chew Toy', html)
        self.assertIn('Petzen Test Chew Toy', self._rpc('/petzen/home/products', limit='bad')['html'])
        self.assertIn('Petzen Test Chew Toy', self._rpc('/petzen/home/products', limit=500)['html'])

    # ── Search ───────────────────────────────────────────────────────────────

    def test_search_products(self):
        """The search overlay finds products by name or category."""
        result = self._rpc('/petzen/search', term='Chew Toy')['results']
        self.assertEqual([r['name'] for r in result], ['Petzen Test Chew Toy'])
        item = result[0]
        self.assertEqual(item['url'], self.product.website_url)
        self.assertEqual(item['tag'], 'Dog')
        self.assertTrue(item['product_id'])
        self.assertEqual(item['price_old'], '')
        self.assertEqual(item['badge'], '')
        self.assertFalse(item['is_new'])
        self.assertTrue(self._rpc('/petzen/search', term='')['results'])
        self.assertEqual(self._rpc('/petzen/search', term='zzzz-no-match')['results'], [])
        self.assertTrue(self._rpc('/petzen/search', term='Dog', limit=500)['results'])

    def test_search_products_discount_and_ribbon(self):
        """A discounted price shows a percentage badge, a ribbon marks new products."""
        pricelist = self.website.pricelist_id
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': self.product.id,
            'compute_price': 'percentage',
            'percent_price': 25,
        })
        pricelist.discount_policy = 'without_discount'
        item = self._rpc('/petzen/search', term='Chew Toy')['results'][0]
        self.assertEqual(item['badge'], '−25%')
        self.assertTrue(item['price_old'])
        pricelist.discount_policy = 'with_discount'
        ribbon = self.env['product.ribbon'].create({'html': 'New', 'bg_color': '#000', 'text_color': '#fff'})
        self.product.website_ribbon_id = ribbon
        item = self._rpc('/petzen/search', term='Chew Toy')['results'][0]
        self.assertEqual(item['badge'], 'New')
        self.assertTrue(item['is_new'])

    # ── Wishlist ─────────────────────────────────────────────────────────────

    def test_wishlist_unavailable(self):
        """Without the wishlist module the route reports it is unavailable."""
        request_mock = MagicMock()
        request_mock.env = {}
        with patch(CONTROLLER + '.request', request_mock):
            result = PetzenServices().wishlist_toggle(self.product.product_variant_id.id)
        self.assertEqual(result, {'available': False})

    def _skip_without_wishlist(self):
        """Skip the test when website_sale_wishlist is not installed."""
        if 'product.wishlist' not in self.env:
            self.skipTest('website_sale_wishlist is not installed')

    def test_wishlist_unknown_or_unpublished_product(self):
        """A missing or unpublished product cannot be added to the wishlist."""
        self._skip_without_wishlist()
        result = self._rpc('/petzen/wishlist/toggle', product_id=0)
        self.assertTrue(result['available'])
        self.assertFalse(result['in_wishlist'])
        self.product.is_published = False
        result = self._rpc('/petzen/wishlist/toggle', product_id=self.product.product_variant_id.id)
        self.assertFalse(result['in_wishlist'])
        self.assertIn('not available', result['error'])

    def test_wishlist_toggle_public_visitor(self):
        """A visitor can add a product to the wishlist and remove it again."""
        self._skip_without_wishlist()
        variant = self.product.product_variant_id
        added = self._rpc('/petzen/wishlist/toggle', product_id=variant.id)
        self.assertTrue(added['in_wishlist'])
        self.assertEqual(added['product_ids'], [variant.id])
        self.assertEqual(added['count'], 1)
        removed = self._rpc('/petzen/wishlist/toggle', product_id=variant.id)
        self.assertFalse(removed['in_wishlist'])
        self.assertEqual(removed['count'], 0)

    def test_wishlist_toggle_logged_in_user(self):
        """A logged in customer can add a product to the wishlist and remove it again."""
        self._skip_without_wishlist()
        self.authenticate(USER_LOGIN, USER_PASSWORD)
        variant = self.product.product_variant_id
        added = self._rpc('/petzen/wishlist/toggle', product_id=variant.id)
        self.assertTrue(added['in_wishlist'])
        self.assertTrue(self.env['product.wishlist'].search([
            ('partner_id', '=', self.user.partner_id.id), ('product_id', '=', variant.id)]))
        removed = self._rpc('/petzen/wishlist/toggle', product_id=variant.id)
        self.assertFalse(removed['in_wishlist'])

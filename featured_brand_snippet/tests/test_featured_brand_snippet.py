# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase


@tagged('post_install', '-at_install')
class TestFeaturedBrandSnippet(TransactionCase):
    """Test the featured flag, the form view and the snippet template."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['product.brand'].create({'name': 'Timber Craft'})

    def test_01_featured_brand_default_false(self):
        """A new brand is not featured unless the flag is enabled."""
        self.assertFalse(self.brand.is_featured_brand)

    def test_02_featured_brand_toggle(self):
        """The featured flag can be enabled and disabled."""
        self.brand.is_featured_brand = True
        self.assertTrue(self.brand.is_featured_brand)
        self.brand.is_featured_brand = False
        self.assertFalse(self.brand.is_featured_brand)

    def test_03_featured_brand_search(self):
        """Only featured brands are found by the featured filter."""
        other = self.env['product.brand'].create(
            {'name': 'Featured Brand', 'is_featured_brand': True})
        featured = self.env['product.brand'].search(
            [('is_featured_brand', '=', True)])
        self.assertIn(other, featured)
        self.assertNotIn(self.brand, featured)

    def test_04_brand_form_view_has_featured_field(self):
        """The brand form shows the featured brand field."""
        arch = self.env['product.brand'].get_view(view_type='form')['arch']
        self.assertIn('is_featured_brand', arch)

    def test_05_snippet_template_has_demo(self):
        """The snippet shows four demo cards in the Insert a block preview."""
        html = str(self.env['ir.qweb']._render(
            'featured_brand_snippet.product_brand_snippet'))
        self.assertIn('s_product_brand', html)
        self.assertIn('dynamic_snippet_brand', html)
        self.assertIn('id="brands"', html)
        self.assertIn('Product Brands', html)
        self.assertIn('text-center', html)
        self.assertEqual(html.count('o_brand_demo_card'), 4)
        for name in ('Timber Craft', 'Brew House', 'Pure Bloom', 'Tech Nova'):
            self.assertIn(name, html)
        self.assertIn('View Products', html)
        for number in range(1, 5):
            self.assertIn(
                '/featured_brand_snippet/static/src/img/snippets/'
                'demo_brand_%d.png' % number, html)

    def test_06_snippet_registered_in_builder(self):
        """The snippet and its group are added to the website snippets."""
        view = self.env.ref('featured_brand_snippet.external_snippets')
        self.assertEqual(view.inherit_id, self.env.ref('website.snippets'))
        self.assertIn('featured_brand_snippet.product_brand_snippet', view.arch)
        self.assertIn('snippet-group="product_brand"', view.arch)


@tagged('post_install', '-at_install')
class TestFeaturedBrandSnippetHttp(HttpCase):
    """Test the brand JSON route and the brand shop page."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Brand = cls.env['product.brand']
        cls.featured_brand = Brand.create(
            {'name': 'Timber Craft', 'is_featured_brand': True})
        cls.other_brand = Brand.create({'name': 'Plain Brand'})
        Product = cls.env['product.template']
        cls.product = Product.create({
            'name': 'Oak Desk Test',
            'brand_id': cls.featured_brand.id,
            'list_price': 100.0,
            'sale_ok': True,
            'is_published': True,
        })
        cls.unpublished_product = Product.create({
            'name': 'Hidden Desk Test',
            'brand_id': cls.featured_brand.id,
            'list_price': 100.0,
            'sale_ok': True,
            'is_published': False,
        })
        cls.other_product = Product.create({
            'name': 'Plain Chair Test',
            'brand_id': cls.other_brand.id,
            'list_price': 50.0,
            'sale_ok': True,
            'is_published': True,
        })

    def test_01_product_brand_route_returns_featured_only(self):
        """The route returns only featured brands with their id and name."""
        result = self.make_jsonrpc_request('/product_brand', {})
        self.assertEqual(
            result, [{'id': self.featured_brand.id, 'name': 'Timber Craft'}])

    def test_02_product_brand_route_empty(self):
        """The route returns an empty list when no brand is featured."""
        self.featured_brand.is_featured_brand = False
        result = self.make_jsonrpc_request('/product_brand', {})
        self.assertEqual(result, [])

    def test_03_product_brand_route_multiple(self):
        """Every featured brand is returned."""
        self.other_brand.is_featured_brand = True
        result = self.make_jsonrpc_request('/product_brand', {})
        self.assertCountEqual(
            [brand['id'] for brand in result],
            [self.featured_brand.id, self.other_brand.id])

    def test_04_shop_brand_page_shows_brand_products(self):
        """The brand page lists only the published products of the brand."""
        slug = self.env['ir.http']._slug(self.featured_brand)
        response = self.url_open('/shop/brand/%s' % slug)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Oak Desk Test', response.text)
        self.assertNotIn('Hidden Desk Test', response.text)
        self.assertNotIn('Plain Chair Test', response.text)

    def test_05_shop_page_without_brand(self):
        """The normal shop page still works without a brand."""
        response = self.url_open('/shop')
        self.assertEqual(response.status_code, 200)

    def test_06_shop_brand_page_without_products(self):
        """A brand without published products still shows its page."""
        empty_brand = self.env['product.brand'].create(
            {'name': 'Empty Brand', 'is_featured_brand': True})
        slug = self.env['ir.http']._slug(empty_brand)
        response = self.url_open('/shop/brand/%s' % slug)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Oak Desk Test', response.text)
        self.assertNotIn('Plain Chair Test', response.text)

    def test_07_shop_brand_page_pagination(self):
        """The brand page shows one page of products and keeps the brand."""
        self.env['product.template'].create({
            'name': 'Pine Desk Test',
            'brand_id': self.featured_brand.id,
            'list_price': 80.0,
            'sale_ok': True,
            'is_published': True,
        })
        slug = self.env['ir.http']._slug(self.featured_brand)
        first = self.url_open('/shop/brand/%s?ppg=1' % slug)
        second = self.url_open('/shop/brand/%s/page/2?ppg=1' % slug)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        names = ('Oak Desk Test', 'Pine Desk Test')
        shown_first = [name for name in names if name in first.text]
        shown_second = [name for name in names if name in second.text]
        self.assertEqual(len(shown_first), 1)
        self.assertEqual(len(shown_second), 1)
        self.assertNotEqual(shown_first, shown_second)
        self.assertIn('/shop/brand/%s/page/2' % slug, first.text)

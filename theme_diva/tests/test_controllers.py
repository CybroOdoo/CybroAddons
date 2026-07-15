# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields
from odoo.tests.common import HttpCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'theme_diva')
class TestBlogController(HttpCase):
    """Tests for the WebsiteBlog JSON endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a blog and published posts
        cls.blog = cls.env['blog.blog'].create({'name': 'Theme Diva Blog'})
        cls.post1 = cls.env['blog.post'].create({
            'name': 'Published Post 1',
            'blog_id': cls.blog.id,
            'website_published': True,
            'post_date': fields.Datetime.now(),
        })
        cls.post2 = cls.env['blog.post'].create({
            'name': 'Published Post 2',
            'blog_id': cls.blog.id,
            'website_published': True,
            'post_date': fields.Datetime.now(),
        })
        cls.draft_post = cls.env['blog.post'].create({
            'name': 'Draft Post',
            'blog_id': cls.blog.id,
            'website_published': False,
        })

    def _json_post(self, url):
        """Helper: make a JSON-RPC POST to the given route."""
        return self.url_open(
            url,
            data=b'{"jsonrpc":"2.0","method":"call","id":1,"params":{}}',
            headers={'Content-Type': 'application/json'},
        )

    # ------------------------------------------------------------------
    # 1. /get_blog_post (limit 3)
    # ------------------------------------------------------------------

    def test_get_blog_post_returns_json(self):
        resp = self._json_post('/get_blog_post')
        data = resp.json()
        self.assertIn('result', data)

    def test_get_blog_post_has_posts_recent_key(self):
        resp = self._json_post('/get_blog_post')
        result = resp.json().get('result', {})
        self.assertIn('posts_recent', result)

    def test_get_blog_post_limit_three(self):
        """Must return at most 3 posts."""
        # Create extra posts to exceed the limit
        for i in range(3):
            self.env['blog.post'].create({
                'name': f'Extra Post {i}',
                'blog_id': self.blog.id,
                'website_published': True,
                'post_date': fields.Datetime.now(),
            })
        resp = self._json_post('/get_blog_post')
        posts = resp.json().get('result', {}).get('posts_recent', [])
        self.assertLessEqual(len(posts), 3)

    def test_get_blog_post_excludes_unpublished(self):
        """Draft posts must not appear in the response."""
        resp = self._json_post('/get_blog_post')
        posts = resp.json().get('result', {}).get('posts_recent', [])
        names = [p.get('name') for p in posts]
        self.assertNotIn('Draft Post', names)

    def test_get_blog_post_fields_in_each_post(self):
        """Each post dict must contain name, published_date, blog_id, cover_properties."""
        resp = self._json_post('/get_blog_post')
        posts = resp.json().get('result', {}).get('posts_recent', [])
        if posts:
            post = posts[0]
            for key in ('name', 'published_date', 'blog_id', 'cover_properties'):
                self.assertIn(key, post,
                              f"Key '{key}' missing from post dict")

    # ------------------------------------------------------------------
    # 2. /get_blog_posts (limit 4)
    # ------------------------------------------------------------------

    def test_get_blog_posts_returns_200(self):
        resp = self._json_post('/get_blog_posts')
        self.assertEqual(resp.status_code, 200)

    def test_get_blog_posts_has_posts_recent_key(self):
        resp = self._json_post('/get_blog_posts')
        result = resp.json().get('result', {})
        self.assertIn('posts_recent', result)

    def test_get_blog_posts_limit_four(self):
        """Must return at most 4 posts."""
        for i in range(5):
            self.env['blog.post'].create({
                'name': f'Four Limit Post {i}',
                'blog_id': self.blog.id,
                'website_published': True,
                'post_date': fields.Datetime.now(),
            })
        resp = self._json_post('/get_blog_posts')
        posts = resp.json().get('result', {}).get('posts_recent', [])
        self.assertLessEqual(len(posts), 4)

    def test_get_blog_posts_excludes_unpublished(self):
        resp = self._json_post('/get_blog_posts')
        posts = resp.json().get('result', {}).get('posts_recent', [])
        names = [p.get('name') for p in posts]
        self.assertNotIn('Draft Post', names)

    def test_get_blog_posts_fields_in_each_post(self):
        resp = self._json_post('/get_blog_posts')
        posts = resp.json().get('result', {}).get('posts_recent', [])
        if posts:
            for key in ('name', 'published_date', 'blog_id', 'cover_properties'):
                self.assertIn(key, posts[0])


@tagged('post_install', '-at_install', 'theme_diva')
class TestProductControllers(HttpCase):
    """Tests for the WebsiteProduct, FeaturedProduct, and MainProduct controllers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product1 = cls.env['product.template'].create({
            'name': 'Featured Product Alpha',
            'type': 'service',
            'is_published': True,
        })
        cls.product2 = cls.env['product.template'].create({
            'name': 'Featured Product Beta',
            'type': 'service',
            'is_published': True,
        })
        # Create a published featured list
        cls.featured = cls.env['product.featured'].create({
            'name': 'Test Featured List',
            'website_published': True,
            'featured_list_ids': [
                (0, 0, {'product_id': cls.product1.id}),
                (0, 0, {'product_id': cls.product2.id}),
            ],
        })

    def _json_post(self, url):
        return self.url_open(
            url,
            data=b'{"jsonrpc":"2.0","method":"call","id":1,"params":{}}',
            headers={'Content-Type': 'application/json'},
        )

    # ------------------------------------------------------------------
    # 3. /get_featured_product (limit 4)
    # ------------------------------------------------------------------

    def test_get_featured_product_returns_200(self):
        resp = self._json_post('/get_featured_product')
        self.assertEqual(resp.status_code, 200)

    def test_get_featured_product_has_featured_products1_key(self):
        resp = self._json_post('/get_featured_product')
        result = resp.json().get('result', {})
        self.assertIn('featured_products1', result)

    def test_get_featured_product_has_currency_symbol_key(self):
        resp = self._json_post('/get_featured_product')
        result = resp.json().get('result', {})
        self.assertIn('currency_symbol', result)

    def test_get_featured_product_limit_four(self):
        """Must return at most 4 featured products."""
        resp = self._json_post('/get_featured_product')
        products = resp.json().get('result', {}).get('featured_products1', [])
        self.assertLessEqual(len(products), 4)

    def test_get_featured_product_only_published_lists(self):
        """Only products from published featured lists must be returned."""
        unpublished = self.env['product.featured'].create({
            'name': 'Unpublished List',
            'website_published': False,
        })
        secret_product = self.env['product.template'].create({
            'name': 'Secret Product',
            'type': 'service',
        })
        unpublished.write({
            'featured_list_ids': [(0, 0, {'product_id': secret_product.id})]
        })
        resp = self._json_post('/get_featured_product')
        names = [p.get('name') for p in
                 resp.json().get('result', {}).get('featured_products1', [])]
        self.assertNotIn('Secret Product', names)

    # ------------------------------------------------------------------
    # 4. /get_featured_products (limit 8)
    # ------------------------------------------------------------------

    def test_get_featured_products_returns_200(self):
        resp = self._json_post('/get_featured_products')
        self.assertEqual(resp.status_code, 200)

    def test_get_featured_products_has_featured_products2_key(self):
        resp = self._json_post('/get_featured_products')
        result = resp.json().get('result', {})
        self.assertIn('featured_products2', result)

    def test_get_featured_products_has_currency_symbol_key(self):
        resp = self._json_post('/get_featured_products')
        result = resp.json().get('result', {})
        self.assertIn('currency_symbol', result)

    def test_get_featured_products_limit_eight(self):
        """Must return at most 8 featured products."""
        resp = self._json_post('/get_featured_products')
        products = resp.json().get('result', {}).get('featured_products2', [])
        self.assertLessEqual(len(products), 8)

    def test_get_featured_products_only_published_lists(self):
        """Only products from published featured lists must appear."""
        unpub2 = self.env['product.featured'].create({
            'name': 'Unpublished List 2',
            'website_published': False,
        })
        hidden = self.env['product.template'].create({
            'name': 'Hidden Product', 'type': 'service'
        })
        unpub2.write({'featured_list_ids': [(0, 0, {'product_id': hidden.id})]})
        resp = self._json_post('/get_featured_products')
        names = [p.get('name') for p in
                 resp.json().get('result', {}).get('featured_products2', [])]
        self.assertNotIn('Hidden Product', names)

    # ------------------------------------------------------------------
    # 5. /get_main_product
    # ------------------------------------------------------------------

    def test_get_main_product_returns_200(self):
        resp = self._json_post('/get_main_product')
        self.assertEqual(resp.status_code, 200)

    def test_get_main_product_has_main_products_key(self):
        resp = self._json_post('/get_main_product')
        result = resp.json().get('result', {})
        self.assertIn('main_products', result)

    def test_get_main_product_returns_at_most_one(self):
        """Must return at most 1 product (limit=1 in the controller)."""
        resp = self._json_post('/get_main_product')
        products = resp.json().get('result', {}).get('main_products', [])
        self.assertLessEqual(len(products), 1)

    def test_get_main_product_only_published(self):
        """The returned product must be published (is_published=True)."""
        resp = self._json_post('/get_main_product')
        products = resp.json().get('result', {}).get('main_products', [])
        for p in products:
            self.assertTrue(
                p.get('is_published') or p.get('website_published'),
                "main_product must be published"
            )

    def test_get_main_product_result_is_list(self):
        """main_products value must be a list (from .read())."""
        resp = self._json_post('/get_main_product')
        result = resp.json().get('result', {})
        self.assertIsInstance(result.get('main_products'), list)
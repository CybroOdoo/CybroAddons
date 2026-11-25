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

from odoo.tests import TransactionCase, tagged
from odoo.addons.website_sale.tests.common import MockRequest


@tagged('post_install', '-at_install')
class TestPetzenWebsite(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()
        # The snippets must not accidentally use the demonstration categories.
        cls.env['product.category'].search([]).write({
            'is_pets_category': False,
        })
        cls.root = cls.env['product.category'].create({
            'name': 'Petzen Test Root'})
        cls.dog_categ = cls.env['product.category'].create({
            'name': 'Dog Supplies', 'parent_id': cls.root.id,
            'is_pets_category': True,
        })
        cls.unknown_categ = cls.env['product.category'].create({
            'name': 'Reptiles', 'parent_id': cls.root.id})
        cls.sub_categ = cls.env['product.category'].create({
            'name': 'Dog Toys', 'parent_id': cls.dog_categ.id})
        cls.public_dogs = cls.env['product.public.category'].create({
            'name': 'Test Hounds'})
        cls.product = cls.env['product.template'].create({
            'name': 'Dog Bone',
            'list_price': 10.0,
            'categ_id': cls.dog_categ.id,
            'is_published': True,
            'sale_ok': True,
            'public_categ_ids': [(6, 0, cls.public_dogs.ids)],
        })

    # ── category selection / domain ────────────────────────────────────

    def test_snippet_category_field(self):
        self.assertIn('is_pets_category',
                      self.env['product.category']._fields)

    def test_product_domain(self):
        domain = self.website._petzen_product_domain()
        products = self.env['product.template'].search(domain)
        self.assertIn(self.product, products)

    def _snippet_products(self, limit=12):
        """The product snippet prices are calculated in a website request."""
        with MockRequest(self.env, website=self.website):
            return self.website._petzen_snippet_products(limit=limit)

    # ── public category / shop url ─────────────────────────────────────

    def test_public_category_exact(self):
        self.assertEqual(
            self.website._petzen_public_category('Test Hounds'), self.public_dogs)

    def test_public_category_plural_fallback(self):
        self.assertEqual(
            self.website._petzen_public_category('Test Hound'), self.public_dogs)

    def test_public_category_empty_name(self):
        self.assertFalse(self.website._petzen_public_category(''))

    def test_shop_url_with_category(self):
        url = self.website._petzen_shop_url('Test Hounds')
        self.assertTrue(url.startswith('/shop/category/'))

    def test_shop_url_with_given_category(self):
        url = self.website._petzen_shop_url('Anything', self.public_dogs)
        self.assertTrue(url.startswith('/shop/category/'))

    def test_shop_url_search_fallback(self):
        url = self.website._petzen_shop_url('Reptiles & Co')
        self.assertEqual(url, '/shop?search=Reptiles%20%26%20Co')

    def test_shop_url_empty_name(self):
        self.assertEqual(self.website._petzen_shop_url(''), '/shop?search=')

    # ── category key ───────────────────────────────────────────────────

    def test_category_key_direct_child(self):
        self.assertEqual(
            self.website._petzen_category_key(self.dog_categ),
            f'c{self.dog_categ.id}')

    def test_category_key_sub_category_uses_top_level(self):
        self.assertEqual(
            self.website._petzen_category_key(self.sub_categ),
            f'c{self.dog_categ.id}')

    # ── category cards ─────────────────────────────────────────────────

    def test_category_cards(self):
        cards = self.website._petzen_category_cards()
        names = {c['name'] for c in cards}
        self.assertIn('Dog Supplies', names)
        self.assertNotIn('Reptiles', names)
        dog = next(c for c in cards if c['name'] == 'Dog Supplies')
        self.assertEqual(dog['icon'], 'lucide:dog')
        self.assertIn('dog.avif', dog['image'])
        self.assertEqual(dog['count'], 1)

        self.unknown_categ.is_pets_category = True
        cards = self.website._petzen_category_cards()
        default = next(c for c in cards if c['name'] == 'Reptiles')
        self.assertEqual(default['icon'], 'lucide:paw-print')

    def test_category_cards_limit(self):
        self.assertLessEqual(
            len(self.website._petzen_category_cards(limit=1)), 1)

    def test_category_cards_with_public_category(self):
        self.env['product.public.category'].create({'name': 'Dog Supplies'})
        cards = self.website._petzen_category_cards()
        dog = next(c for c in cards if c['name'] == 'Dog Supplies')
        self.assertTrue(dog['url'].startswith('/shop/category/'))

    def test_category_cards_custom_image(self):
        # 1x1 transparent PNG
        png = ('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4'
               '2mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')
        self.dog_categ.image_1920 = png
        cards = self.website._petzen_category_cards()
        dog = next(c for c in cards if c['name'] == 'Dog Supplies')
        self.assertIn('/web/image/product.category/', dog['image'])

    def test_category_cards_without_selected_categories(self):
        self.dog_categ.is_pets_category = False
        self.assertEqual(self.website._petzen_category_cards(), [])

    # ── snippet products ───────────────────────────────────────────────

    def test_snippet_products_structure(self):
        result = self._snippet_products()
        self.assertIn('tabs', result)
        self.assertIn('products', result)
        self.assertIn('wishlist', result)
        self.assertIsInstance(result['products'], list)

    def test_snippet_products_contains_product(self):
        result = self._snippet_products()
        ids = [p['id'] for p in result['products']]
        self.assertIn(self.product.id, ids)
        item = next(p for p in result['products']
                    if p['id'] == self.product.id)
        self.assertEqual(item['name'], 'Dog Bone')
        self.assertIn('url', item)
        self.assertIn('price', item)

    def test_snippet_products_with_discount_and_ribbon(self):
        ribbon = self.env['product.ribbon'].create({'name': 'Sale'})
        self.product.website_ribbon_id = ribbon
        result = self._snippet_products()
        item = next(p for p in result['products']
                    if p['id'] == self.product.id)
        self.assertTrue(item['badge'])

    def test_snippet_products_excludes_unselected_categories(self):
        # Products outside selected categories must not fall back into the block.
        self.product.write({
            'categ_id': self.env['product.category'].create({
                'name': 'Unselected Category'}).id,
            'public_categ_ids': [(5, 0, 0)],
        })
        result = self._snippet_products()
        ids = [p['id'] for p in result['products']]
        self.assertNotIn(self.product.id, ids)

    def test_snippet_products_limit(self):
        result = self._snippet_products(limit=1)
        self.assertLessEqual(len(result['products']), 1)

    def test_snippet_products_tabs(self):
        result = self._snippet_products()
        self.assertIn(f'c{self.dog_categ.id}',
                      [t['key'] for t in result['tabs']])

    def test_snippet_products_includes_selected_category_descendants(self):
        self.product.categ_id = self.sub_categ
        result = self._snippet_products()
        item = next(p for p in result['products']
                    if p['id'] == self.product.id)
        self.assertEqual(item['key'], f'c{self.dog_categ.id}')
        self.assertEqual(item['tag'], 'Dog Supplies')

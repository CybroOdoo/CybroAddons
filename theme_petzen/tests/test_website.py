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

from odoo.addons.http_routing.models.ir_http import slug
from odoo.tests import TransactionCase, tagged

from .test_product_category import PIXEL


@tagged('post_install', '-at_install', 'theme_petzen')
class TestWebsite(TransactionCase):
    """Test the website helpers that feed the category and product sections."""

    @classmethod
    def setUpClass(cls):
        """Prepare the website, the Petzen root category and one published product."""
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()
        cls.root = cls.env.ref('theme_petzen.product_category_petzen')
        cls.dog = cls.env.ref('theme_petzen.product_category_dog')
        cls.product = cls.env['product.template'].create({
            'name': 'Petzen Dog Bone',
            'categ_id': cls.dog.id,
            'is_published': True,
            'sale_ok': True,
        })

    def test_root_category(self):
        """The root category is the one created by the theme data."""
        self.assertEqual(self.website._petzen_root_category(), self.root)

    def test_product_domain(self):
        """The domain keeps only published products."""
        domain = self.website._petzen_product_domain()
        self.assertIn(('is_published', '=', True), domain)
        self.assertIn(self.product, self.env['product.template'].search(domain))

    def test_products_in_petzen_tree(self):
        """Products of the Petzen tree are returned first."""
        other = self.env['product.template'].create({
            'name': 'Other Product', 'is_published': True, 'sale_ok': True})
        products = self.website._petzen_products()
        self.assertIn(self.product, products)
        self.assertNotIn(other, products)
        self.assertEqual(len(self.website._petzen_products(limit=1)), 1)

    def test_products_fallback(self):
        """Every published product is returned when the Petzen tree has none."""
        self.product.categ_id = self.env.ref('product.product_category_all')
        products = self.website._petzen_products()
        self.assertIn(self.product, products)

    def test_products_without_root(self):
        """Without the root category every published product is returned."""
        self.env['ir.model.data'].search([
            ('module', '=', 'theme_petzen'), ('name', '=', 'product_category_petzen')]).unlink()
        self.assertFalse(self.website._petzen_root_category())
        self.assertIn(self.product, self.website._petzen_products())
        self.assertEqual(self.website._petzen_category_cards(), [])

    def test_category_cards(self):
        """The tiles follow the Petzen sub-categories with icon, link and count."""
        cards = self.website._petzen_category_cards()
        self.assertEqual(len(cards), 5)
        dog = cards[0]
        self.assertEqual(dog['name'], 'Dog')
        self.assertEqual(dog['icon'], 'lucide:dog')
        self.assertEqual(dog['key'], 'dog')
        self.assertEqual(dog['category'], self.dog)
        self.assertTrue(dog['image'].startswith('https://'))
        self.assertIn('/shop/category/', dog['url'])
        self.assertEqual(len(self.website._petzen_category_cards(limit=2)), 2)

    def test_category_cards_default_style_and_image(self):
        """A category without a known keyword uses the default icon and its own image."""
        categ = self.env['product.category'].create({
            'name': 'Zebra Corner', 'parent_id': self.root.id, 'image_1920': PIXEL})
        card = [c for c in self.website._petzen_category_cards(limit=20) if c['category'] == categ][0]
        self.assertEqual(card['icon'], 'lucide:paw-print')
        self.assertIn('/web/image/product.category/%s/image_1920' % categ.id, card['image'])
        self.assertIn('/shop?search=Zebra%20Corner', card['url'])
        self.assertEqual(card['count'], 0)

    def test_category_cards_count_without_public_category(self):
        """The product count uses the internal category when no eCommerce category matches."""
        categ = self.env['product.category'].create({'name': 'Lizard', 'parent_id': self.root.id})
        self.env['product.template'].create({
            'name': 'Lizard Lamp', 'categ_id': categ.id, 'is_published': True, 'sale_ok': True})
        card = [c for c in self.website._petzen_category_cards(limit=20) if c['category'] == categ][0]
        self.assertEqual(card['count'], 1)

    def test_shop_url(self):
        """The shop url opens the eCommerce category, else a shop search."""
        public = self.env.ref('theme_petzen.public_category_dog')
        self.assertEqual(self.website._petzen_shop_url('Dog'), '/shop/category/%s' % slug(public))
        self.assertEqual(self.website._petzen_shop_url('Dog', public), '/shop/category/%s' % slug(public))
        self.assertEqual(self.website._petzen_shop_url('Unknown pet'), '/shop?search=Unknown%20pet')
        self.assertEqual(self.website._petzen_shop_url(''), '/shop?search=')
        self.assertEqual(self.website._petzen_shop_url(False), '/shop?search=')

    def test_public_category(self):
        """The eCommerce category matches the exact name, then the plural, else nothing."""
        PublicCategory = self.env['product.public.category']
        self.assertEqual(self.website._petzen_public_category('dog'), self.env.ref('theme_petzen.public_category_dog'))
        plural = PublicCategory.create({'name': 'Rabbits'})
        self.assertEqual(self.website._petzen_public_category('Rabbit'), plural)
        self.assertFalse(self.website._petzen_public_category('No Such Pet'))
        self.assertFalse(self.website._petzen_public_category(''))

    def test_category_key(self):
        """The filter key is the lower-cased top-level Petzen category name."""
        sub = self.env['product.category'].create({'name': 'Puppy Food', 'parent_id': self.dog.id})
        self.assertEqual(self.website._petzen_category_key(self.dog), 'dog')
        self.assertEqual(self.website._petzen_category_key(sub), 'dog')
        self.assertEqual(self.website._petzen_category_key(self.root), 'petzen')

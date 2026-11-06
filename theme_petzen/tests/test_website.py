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

from unittest.mock import MagicMock, patch
from urllib.parse import quote as url_quote

from odoo.tests import TransactionCase, tagged
from odoo.tools import format_amount

from odoo.addons.theme_petzen.models.website import PETZEN_CATEGORY_STYLES

@tagged('post_install', '-at_install', 'theme_petzen')
class TestPetzenWebsite(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        site = cls.env['website'].create({'name': 'Petzen Test'})
        cls.website = site.with_context(website_id=site.id)
        cls.website_cls = cls.env.registry['website']
        cls.template_cls = cls.env.registry['product.template']
        # start without "Pets Categories" (e.g. the ones of the theme data)
        cls.env['product.category'].search(
            [('is_pets_category', '=', True)]).is_pets_category = False

    # -- helpers -------------------------------------------------------
    def _start(self, patcher):
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def _categ(self, name, parent=None, pets=False):
        return self.env['product.category'].create(
            {'name': name, 'parent_id': parent.id if parent else False,
             'is_pets_category': pets})

    def _public(self, name, parent=None):
        return self.env['product.public.category'].create(
            {'name': name, 'parent_id': parent.id if parent else False})

    def _product(self, name, categ=None, public=None, **kw):
        vals = {'name': name, 'list_price': 100.0, 'sale_ok': True,
                'is_published': True}
        if categ:
            vals['categ_id'] = categ.id
        if public:
            vals['public_categ_ids'] = [(6, 0, public.ids)]
        vals.update(kw)
        return self.env['product.template'].create(vals)

    # -- "Pets Category" lookup ----------------------------------------
    def test_pets_categories(self):
        dogs = self._categ('Dogs', pets=True)
        cats = self._categ('Cats', pets=True)
        self._categ('Not Pets')
        self.assertEqual(self.website._petzen_pets_categories(), dogs | cats)
        self.assertEqual(self.website._petzen_pets_categories(limit=1), dogs)

    def test_pets_category_of_sub_category(self):
        root = self._categ('Root')
        dogs = self._categ('Dogs', root, pets=True)
        puppies = self._categ('Puppies', dogs)
        find = self.website._petzen_pets_category
        self.assertEqual(find(dogs), dogs)
        self.assertEqual(find(puppies), dogs)       # closest flagged parent
        self.assertFalse(find(root))
        self.assertFalse(find(self.env['product.category']))

    # -- _petzen_is_direct_add -----------------------------------------
    def test_is_direct_add(self):
        def fake(type_='consu', variants=1, possible=True):
            product = MagicMock(type=type_, product_variant_count=variants)
            product._is_add_to_cart_possible.return_value = possible
            return product

        direct = self.website._petzen_is_direct_add
        self.assertTrue(direct(fake()))
        self.assertFalse(direct(fake(type_='combo')))
        self.assertFalse(direct(fake(variants=2)))
        self.assertFalse(direct(fake(possible=False)))

    # -- category lookup / url -----------------------------------------
    def test_public_category_lookup(self):
        exact = self._public('Quokka')
        plural = self._public('Zorbos')
        find = self.website._petzen_public_category
        self.assertEqual(find('quokka'), exact)       # case-insensitive
        self.assertEqual(find('Zorbo'), plural)       # "Zorbo" -> "Zorbos"
        self.assertFalse(find('No Such Category'))
        self.assertFalse(find(''))

    def test_shop_url(self):
        categ = self._public('Url Category')
        slug = self.env['ir.http']._slug(categ)
        self.assertEqual(self.website._petzen_shop_url('Url Category'),
                         '/shop/category/%s' % slug)
        self.assertEqual(self.website._petzen_shop_url('Cats & Dogs'),
                         '/shop?search=%s' % url_quote('Cats & Dogs'))


    # -- _petzen_category_cards ----------------------------------------
    def test_category_cards_without_pets_categories(self):
        self._categ('Not Pets')
        self.assertEqual(self.website._petzen_category_cards(), [])

    def test_category_cards_data(self):
        keyword, icon, image = PETZEN_CATEGORY_STYLES[0]   # e.g. "dog"
        name = '%s Zone' % keyword.title()
        categ = self._categ(name, pets=True)
        self._categ('Not Pets')
        self._product('P1', categ=categ)
        self._product('P2', categ=self._categ('Sub', categ))
        self._product('P3 hidden', categ=categ, is_published=False)
        cards = self.website._petzen_category_cards()
        self.assertEqual([card['name'] for card in cards], [name])
        card = cards[0]
        self.assertEqual(card['icon'], icon)
        self.assertEqual(card['image'], image)
        self.assertEqual(card['count'], 2)
        self.assertEqual(card['url'], '/shop?search=%s' % url_quote(name))

    def test_category_cards_limit(self):
        self._categ('First Pets', pets=True)
        self._categ('Second Pets', pets=True)
        cards = self.website._petzen_category_cards(limit=1)
        self.assertEqual([card['name'] for card in cards], ['First Pets'])

    # -- _petzen_snippet_products --------------------------------------
    def _snippet_setup(self):
        self.tab = self._categ('Snip Dogs', pets=True)
        self.empty_tab = self._categ('Snip Cats', pets=True)
        self.prices = {}
        self._start(patch.object(
            self.template_cls, '_get_sales_prices', autospec=True,
            side_effect=lambda products, website: {
                pid: self.prices[pid]
                for pid in products.ids if pid in self.prices}))
        self._start(patch.object(
            self.website_cls, '_petzen_card_buttons', return_value={}))
        self._start(patch.object(
            self.website_cls, '_petzen_wishlist_templates',
            return_value=self.env['product.template']))
        self._start(patch.object(
            self.website_cls, '_petzen_is_direct_add', return_value=True))

    def test_snippet_products_and_tabs(self):
        self._snippet_setup()
        product = self._product(
            'Dog Toy', categ=self._categ('Snip Puppies', self.tab),
            list_price=80.0)
        self._product('Not In Petzen', categ=self._categ('Snip Other'))
        data = self.website._petzen_snippet_products()
        self.assertEqual([p['name'] for p in data['products']], ['Dog Toy'])
        card = data['products'][0]
        self.assertEqual(card['id'], product.id)
        self.assertEqual(card['key'], 'c%s' % self.tab.id)
        self.assertEqual(card['tag'], 'Snip Dogs')
        self.assertEqual(
            card['price'],
            format_amount(self.env, 80.0, self.website.currency_id))
        # only the tabs with products
        self.assertEqual(
            data['tabs'], [{'key': 'c%s' % self.tab.id, 'name': 'Snip Dogs'}])

    def test_snippet_discount_badge(self):
        self._snippet_setup()
        product = self._product('Sale Item', categ=self.tab)
        self.prices[product.id] = {'price_reduce': 80.0, 'base_price': 100.0}
        card = self.website._petzen_snippet_products()['products'][0]
        self.assertEqual(card['badge'], '\u221220%')
        self.assertEqual(
            card['price_old'],
            format_amount(self.env, 100.0, self.website.currency_id))

    def test_snippet_without_pets_categories_is_empty(self):
        self._product('Anything', categ=self._categ('Not Pets'))
        self.assertEqual(self.website._petzen_snippet_products(),
                         {'tabs': [], 'products': []})

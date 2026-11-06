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

from urllib.parse import quote as url_quote

from odoo import models
from odoo.tools import format_amount

# Look of the category tiles / tabs, keyed by a keyword of the category name.
# (icon, fallback image) — the fallback is used when the category has no image.
PETZEN_CATEGORY_STYLES = [
    ('dog', 'lucide:dog',
     '/theme_petzen/static/src/images/dog.avif'),
    ('cat', 'lucide:cat',
     '/theme_petzen/static/src/images/cat.avif'),
    ('bird', 'lucide:bird',
     '/theme_petzen/static/src/images/bird.avif'),
    ('small', 'lucide:rat',
     '/theme_petzen/static/src/images/rat.avif'),
    ('fish', 'lucide:fish',
     '/theme_petzen/static/src/images/fish.avif'),
    ('access', 'lucide:bone',
     '/theme_petzen/static/src/images/bone.avif'),
]
PETZEN_DEFAULT_STYLE = (
    'lucide:paw-print',
    '/theme_petzen/static/src/images/print.avif',
)


class Website(models.Model):
    """Extend websites with Petzen category and product helpers."""
    _inherit = 'website'

    def _petzen_pets_categories(self, limit=None):
        """Return the internal product categories flagged "Pets Category"."""
        return self.env['product.category'].sudo().search(
            [('is_pets_category', '=', True)], order='id', limit=limit)

    def _petzen_pets_category(self, categ):
        """Return the "Pets Category" of a product category: itself or its
        closest flagged parent (empty recordset when there is none)."""
        categ = categ.sudo()
        while categ and not categ.is_pets_category:
            categ = categ.parent_id
        return categ

    def _petzen_product_domain(self):
        """Return the domain of the products sold
        and published on this website."""
        self.ensure_one()
        return self.sale_product_domain() + [('is_published', '=', True)]

    def _petzen_is_direct_add(self, product):
        """Return whether a product can be added to the cart in one click.

        Same rule as the Odoo 18 product snippets: a single sellable variant.
        Combo products are excluded, they open Odoo's combo configurator (from
        the product page) like on the standard shop."""
        return (
                product.type != 'combo'
                and product.product_variant_count == 1
                and product._is_add_to_cart_possible()
        )

    def _petzen_wishlist_templates(self):
        """Return the product templates of the current
        visitor's wishlist (empty when website_sale_wishlist is not installed),
        like the shop controller."""
        if 'product.wishlist' not in self.env:
            return self.env['product.template']
        return self.env['product.wishlist'].current().product_id.product_tmpl_id

    def _petzen_card_buttons(self, product, price_reduce, wishlist_templates):
        """Return the data of the "Add" and wishlist buttons of a product card.
        Same rules as the buttons of the shop product tiles of Odoo 18
        (website_sale.products_add_to_cart,
         website_sale_wishlist.add_to_wishlist),so the cards are handled by the
         standard website_sale JS: the "Add" button goes through the
         product / combo configurator when needed."""
        variant_id = product._get_first_possible_variant_id()
        return {
            'template_id': product.id,
            'variant_id': variant_id,
            'show_add': bool(
                ((variant_id and price_reduce) or
                 not self.prevent_zero_price_sale)
                and product._website_show_quick_add()
            ),
            'show_wishlist': bool(
                'product.wishlist' in self.env and variant_id
                and product.type != 'combo'
            ),
            'in_wishlist': product in wishlist_templates,
        }

    def _petzen_category_cards(self, limit=5):
        """Data for the category bento tiles: one entry per "Pets Category"."""
        self.ensure_one()
        categories = self._petzen_pets_categories(limit=limit)
        domain = self._petzen_product_domain()
        cards = []
        for categ in categories:
            name = categ.name or ''
            icon, image = PETZEN_DEFAULT_STYLE
            for keyword, kw_icon, kw_image in PETZEN_CATEGORY_STYLES:
                if keyword in name.lower():
                    icon, image = kw_icon, kw_image
                    break
            if categ.image_1920:
                image = f'/web/image/product.category/{categ.id}/image_1920'
            # the shop filters on eCommerce (public) categories: open the
            # one with the same name, else search the shop for the category name
            public_categ = self._petzen_public_category(name)
            url = self._petzen_shop_url(name, public_categ)
            if public_categ:
                count_domain = domain + [
                    ('public_categ_ids', 'child_of', public_categ.id)]
            else:
                count_domain = domain + [('categ_id', 'child_of', categ.id)]
            cards.append({
                'name': name,
                'icon': icon,
                'image': image,
                'url': url,
                'count': self.env['product.template'].search_count(
                    count_domain),
            })
        return cards

    def _petzen_shop_url(self, name, public_categ=None):
        """Shop URL for a category name: its eCommerce category page,
         else a shop search."""
        self.ensure_one()
        if public_categ is None:
            public_categ = self._petzen_public_category(name)
        if public_categ:
            return f"/shop/category/{self.env['ir.http']._slug(public_categ)}"
        return f'/shop?search={url_quote(name or "")}'

    def _petzen_public_category(self, name):
        """eCommerce category of this website matching an internal category name
        (exact name first, then e.g. "Dog" → "Dogs")."""
        self.ensure_one()
        if not name:
            return self.env['product.public.category']
        public_category_model = self.env['product.public.category']
        domain = self.website_domain()
        return (
                public_category_model.search(
                    domain + [('name', '=ilike', name)], limit=1)
                or public_category_model.search(
            domain + [('name', '=ilike', name + 's')], limit=1
        )
        )

    # ── "Petzen Products" snippet (static/src/js/products_snippet.js) ────────

    def _petzen_snippet_products(self, limit=12):
        """Tabs + product cards of the Petzen Products snippet.

        Only the products of the internal categories flagged "Pets Category"
        (sub-categories too) are shown, one tab per flagged category."""
        self.ensure_one()
        tab_categories = self._petzen_pets_categories()
        if not tab_categories:
            return {'tabs': [], 'products': []}

        product_model = self.env['product.template']
        domain = self._petzen_product_domain() + [
            ('categ_id', 'child_of', tab_categories.ids)]
        products = product_model.search(domain, order='website_sequence, id',
                                        limit=limit)

        prices = products._get_sales_prices(self)
        currency = self.currency_id
        wishlist_templates = self._petzen_wishlist_templates()
        data = []
        for product in products:
            price = prices.get(product.id, {})
            price_reduce = price.get('price_reduce', product.list_price)
            base_price = price.get('base_price')
            discount = int(round(
                100 - price_reduce * 100 / base_price)) if base_price else 0
            direct_add = self._petzen_is_direct_add(product)
            rating = int(
                round(product.rating_avg or 0)
            ) if 'rating_avg' in product._fields else 0
            # label and tab of the card: its "Pets Category"
            pets_categ = self._petzen_pets_category(product.categ_id)
            data.append({
                'id': product.id,
                'name': product.name,
                'url': product.website_url,
                'image': f'/web/image/product.template/{product.id}/image_512',
                'tag': pets_categ.name or '',
                'key': f'c{pets_categ.id}' if pets_categ else '',
                'price': format_amount(self.env, price_reduce, currency),
                'price_old': format_amount(self.env, base_price,
                                           currency) if base_price else '',
                'badge': (
                    f'−{discount}%'
                    if discount > 0 else product.website_ribbon_id.name or ''
                ),
                'is_new': discount <= 0 and bool(product.website_ribbon_id),
                'rating': rating,
                'rating_count': product.rating_count
                if 'rating_count' in product._fields else 0,
                'product_id': product.product_variant_id.id if direct_add else False,
                'buttons': self._petzen_card_buttons(
                    product, price_reduce,wishlist_templates),
            })
        used_keys = {item['key'] for item in data}
        tabs = [
            {'key': f'c{categ.id}', 'name': categ.name}
            for categ in tab_categories
            if f'c{categ.id}' in used_keys
        ]
        return {'tabs': tabs, 'products': data}

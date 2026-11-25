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
from odoo.fields import Domain
from odoo.tools import format_amount

# Look of the category tiles / tabs, keyed by a keyword of the category name:
# (keyword, icon, fallback image). The image is used when the category has none.
PETZEN_CATEGORY_STYLES = [
    ('dog', 'lucide:dog', '/theme_petzen/static/src/images/dog.avif'),
    ('cat', 'lucide:cat', '/theme_petzen/static/src/images/cat.avif'),
    ('bird', 'lucide:bird', '/theme_petzen/static/src/images/bird.avif'),
    ('small', 'lucide:rat', '/theme_petzen/static/src/images/rat.avif'),
    ('fish', 'lucide:fish', '/theme_petzen/static/src/images/fish.avif'),
    ('access', 'lucide:bone', '/theme_petzen/static/src/images/bone.avif'),
]
PETZEN_DEFAULT_STYLE = (
    'lucide:paw-print',
    '/theme_petzen/static/src/images/print.avif',
)


class Website(models.Model):
    """Data of the Petzen theme blocks: category tiles, shop links and the
    product cards of the "Petzen Products" snippet."""
    _inherit = 'website'

    def _petzen_snippet_categories(self):
        """Return categories explicitly selected for the Petzen snippets.

        This deliberately does not depend on the demonstration category tree:
        a website manager can select any internal product category from its
        form, including a category created after the theme was installed.
        """
        self.ensure_one()
        return self.env['product.category'].sudo().search(
            [('is_pets_category', '=', True)], order='name, id')

    def _petzen_product_domain(self):
        """Return the domain of the products sold
        and published on this website."""
        self.ensure_one()
        return Domain.AND([
            self.sale_product_domain(),
            [('is_published', '=', True)],
        ])

    def _petzen_category_cards(self, limit=5):
        """Return tile data for categories selected for Petzen snippets."""
        self.ensure_one()
        categories = self._petzen_snippet_categories()[:limit]
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
            # The shop filters on eCommerce (public) categories: open the one
            # with the same name, else search the shop for the category name.
            public_categ = self._petzen_public_category(name)
            count_domain = Domain.AND([
                domain, [('categ_id', 'child_of', categ.id)]])
            cards.append({
                'category': categ,
                'name': name,
                'key': self._petzen_category_key(categ),
                'icon': icon,
                'image': image,
                'url': self._petzen_shop_url(name, public_categ),
                'count': self.env['product.template'].search_count(count_domain),
            })
        return cards

    def _petzen_shop_url(self, name, public_categ=None):
        """Return the shop url of a category name: its eCommerce category
        page, else a shop search on the name."""
        self.ensure_one()
        if public_categ is None:
            public_categ = self._petzen_public_category(name)
        if public_categ:
            return f"/shop/category/{self.env['ir.http']._slug(public_categ)}"
        return f"/shop?search={url_quote(name or '')}"

    def _petzen_public_category(self, name):
        """Return the eCommerce category of this website matching an internal
        category name (exact name first, then e.g. "Dog" → "Dogs")."""
        self.ensure_one()
        PublicCategory = self.env['product.public.category']
        if not name:
            return PublicCategory
        domain = self.website_domain()
        return (PublicCategory.search(
            Domain.AND([domain, [('name', '=ilike', name)]]), limit=1)
            or PublicCategory.search(
                Domain.AND([domain,
                            [('name', '=ilike', f'{name}s')]]), limit=1))

    def _petzen_category_key(self, categ):
        """Return the product-tab key of a selected category or its ancestor."""
        categ = categ.sudo()
        while categ:
            if categ.is_pets_category:
                return f'c{categ.id}'
            categ = categ.parent_id
        return ''

    # ── "Petzen Products" snippet (static/src/js/products_snippet.js) ────────

    def _petzen_snippet_products(self, limit=12):
        """Return the tabs and product cards of the "Petzen Products" snippet.

        Products are selected exclusively from internal product categories with
        ``is_pets_category`` enabled (including their descendants). The same
        categories provide the tabs, so category and product snippets always
        reflect the website manager's selection."""
        self.ensure_one()
        tab_categories = self._petzen_snippet_categories()

        Product = self.env['product.template']
        domain = self._petzen_product_domain()
        products = Product.browse()
        if tab_categories:
            products = Product.search(
                Domain.AND([domain, [
                    ('categ_id', 'child_of', tab_categories.ids)
                ]]),
                order='website_sequence, id', limit=limit)

        def product_key(product):
            """Return the key of the selected internal category for a product."""
            return self._petzen_category_key(product.categ_id)

        prices = products._get_sales_prices(self)
        currency = self.currency_id
        wishlist_ids = []
        wishlist_enabled = 'product.wishlist' in self.env
        if wishlist_enabled:
            wishlist_ids = self.env['product.wishlist'].current().product_id.ids
        data = []
        for product in products:
            price = prices.get(product.id, {})
            price_reduce = price.get('price_reduce', product.list_price)
            base_price = price.get('base_price')
            discount = int(round(
                100 - price_reduce * 100 / base_price)) if base_price else 0
            # same rule as Odoo's shop tiles (website_sale.shop_product_buttons):
            # the "Add" button is shown whenever the product can be added, the
            # cart service then opens the variant / combo / optional products
            # configurator if needed
            can_add = (product._is_add_to_cart_possible()
                       and product._website_show_quick_add())
            direct_add = can_add and product.product_variant_count == 1
            rating = int(round(product.sudo().rating_avg or 0)) \
                if 'rating_avg' in product._fields else 0
            categories = product.sudo().public_categ_ids
            snippet_category = product.sudo().categ_id
            while snippet_category and not snippet_category.is_pets_category:
                snippet_category = snippet_category.parent_id
            data.append({
                'id': product.id,
                'name': product.name,
                'url': product.website_url,
                'image': f'/web/image/product.template/{product.id}/image_512',
                'tag': (snippet_category.name
                        or categories[:1].name
                        or product.sudo().categ_id.name or ''),
                'key': product_key(product) or '',
                'price': format_amount(self.env, price_reduce, currency),
                'price_old': format_amount(self.env, base_price, currency)
                if base_price else '',
                'badge': f'−{discount}%' if discount > 0
                else (product.website_ribbon_id.name or ''),
                'is_new': discount <= 0 and bool(product.website_ribbon_id),
                'rating': rating,
                'rating_count': product.rating_count
                if 'rating_count' in product._fields else 0,
                'can_add': bool(can_add),
                # variant only when there is a single one (else chosen in the
                # configurator)
                'product_id': product.product_variant_id.id if direct_add else False,
                'template_id': product.id,
                'variant_id': product.product_variant_id.id,
                'product_type': product.type,
                'in_wishlist': product.product_variant_id.id in wishlist_ids,
            })
        used_keys = {item['key'] for item in data}
        tabs = [{'key': f'c{categ.id}', 'name': categ.name}
                for categ in tab_categories if f'c{categ.id}' in used_keys]
        return {'tabs': tabs, 'products': data, 'wishlist': wishlist_enabled}

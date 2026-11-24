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
from odoo.addons.http_routing.models.ir_http import slug

# Look of the category tiles / tabs, keyed by a keyword of the category name.
# (icon, fallback image) — the fallback is used when the category has no image.
PETZEN_CATEGORY_STYLES = [
    ('dog', 'lucide:dog',
     'https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=800&q=82&auto=format&fit=crop'),
    ('cat', 'lucide:cat',
     'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=600&q=82&auto=format&fit=crop'),
    ('bird', 'lucide:bird',
     'https://images.unsplash.com/photo-1552728089-57bdde30beb3?w=600&q=82&auto=format&fit=crop'),
    ('small', 'lucide:rat',
     'https://images.unsplash.com/photo-1425082661705-1834bfd09dca?w=600&q=82&auto=format&fit=crop'),
    ('fish', 'lucide:fish',
     'https://images.unsplash.com/photo-1520301255226-bf5f144451c1?w=600&q=82&auto=format&fit=crop'),
    ('access', 'lucide:bone',
     'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=600&q=82&auto=format&fit=crop'),
]
PETZEN_DEFAULT_STYLE = (
    'lucide:paw-print',
    'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=600&q=82&auto=format&fit=crop')


class Website(models.Model):
    """Add the helpers that feed the Petzen category and product sections."""
    _inherit = 'website'

    def _petzen_root_category(self):
        """Return the root internal category of the Petzen category tree."""
        return self.env.ref('theme_petzen.product_category_petzen', raise_if_not_found=False)

    def _petzen_product_domain(self):
        """Return the domain of the products published on this website."""
        self.ensure_one()
        return self.sale_product_domain() + [('is_published', '=', True)]

    def _petzen_products(self, limit=None):
        """Published products of the Petzen category tree, or every published
        product when that tree is still empty (fresh database)."""
        self.ensure_one()
        Product = self.env['product.template']
        domain = self._petzen_product_domain()
        root = self._petzen_root_category()
        if root:
            products = Product.search(domain + [('categ_id', 'child_of', root.id)], limit=limit)
            if products:
                return products
        return Product.search(domain, limit=limit)

    def _petzen_category_cards(self, limit=5):
        """Data for the category bento tiles and the product tabs."""
        self.ensure_one()
        root = self._petzen_root_category()
        if not root:
            return []
        categories = self.env['product.category'].sudo().search(
            [('parent_id', '=', root.id)], order='id', limit=limit)
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
                image = '/web/image/product.category/%s/image_1920' % categ.id
            # the shop filters on eCommerce (public) categories: open the one with the
            # same name, else search the shop for the category name
            public_categ = self._petzen_public_category(name)
            url = self._petzen_shop_url(name, public_categ)
            if public_categ:
                count_domain = domain + [('public_categ_ids', 'child_of', public_categ.id)]
            else:
                count_domain = domain + [('categ_id', 'child_of', categ.id)]
            cards.append({
                'category': categ,
                'name': name,
                'key': self._petzen_category_key(categ),
                'icon': icon,
                'image': image,
                'url': url,
                'count': self.env['product.template'].search_count(count_domain),
            })
        return cards

    def _petzen_shop_url(self, name, public_categ=None):
        """Shop URL for a category name: its eCommerce category page, else a shop search."""
        self.ensure_one()
        if public_categ is None:
            public_categ = self._petzen_public_category(name)
        if public_categ:
            return '/shop/category/%s' % slug(public_categ)
        return '/shop?search=%s' % url_quote(name or '')

    def _petzen_public_category(self, name):
        """eCommerce category of this website matching an internal category name
        (exact name first, then e.g. "Dog" → "Dogs")."""
        self.ensure_one()
        if not name:
            return self.env['product.public.category']
        PublicCategory = self.env['product.public.category']
        domain = self.website_domain()
        return (PublicCategory.search(domain + [('name', '=ilike', name)], limit=1)
                or PublicCategory.search(domain + [('name', '=ilike', name + 's')], limit=1))

    def _petzen_category_key(self, categ):
        """Filter key of a product category: the name of its top-level Petzen
        category, lower-cased (products of sub-categories filter with their parent)."""
        root = self._petzen_root_category()
        categ = categ.sudo()
        while root and categ.parent_id and categ.parent_id != root:
            categ = categ.parent_id
        return (categ.name or '').strip().lower()

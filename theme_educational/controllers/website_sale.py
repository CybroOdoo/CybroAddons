# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class MyWebsiteSale(WebsiteSale):
    """Controller extending WebsiteSale to support category filtering and recently viewed products."""

    def _update_recently_viewed_products(self, product_id):
        """Add product ID to session and maintain a maximum of 3 recent products.

        :param product_id: Integer ID of the product.template
        :return: List of recently viewed product IDs
        """
        recently_viewed = request.session.get('recently_viewed_products', [])
        recently_viewed = [pid for pid in recently_viewed if pid != product_id]
        recently_viewed.append(product_id)
        recently_viewed = recently_viewed[-3:]

        request.session['recently_viewed_products'] = recently_viewed
        request.session.modified = True
        return recently_viewed

    def _get_recently_viewed_product_ids(self):
        """Return recently viewed product IDs stored in session.

        :return: List of product template IDs
        """
        return request.session.get('recently_viewed_products', [])

    def _get_shop_domain(self, search, category, attrib_values, search_in_description=True):
        """Apply selected category checkboxes and recently viewed filters to shop domain.

        :param search: Search string
        :param category: Selected category record
        :param attrib_values: Selected attribute values
        :param search_in_description: Boolean whether to search in product descriptions
        :return: Computed domain list for searching products
        """
        domain = super()._get_shop_domain(
            search, category, attrib_values, search_in_description
        )

        selected_category_ids = [
            int(x) for x in request.httprequest.args.getlist('category_ids[]') if x.isdigit()
        ]
        is_recent_filter = request.httprequest.args.get('recent') == '1'

        if selected_category_ids:
            category_domain = (
                ['|'] * (len(selected_category_ids) - 1)
                if len(selected_category_ids) > 1 else []
            )
            for cat_id in selected_category_ids:
                category_domain.append(('public_categ_ids', 'in', [cat_id]))
            domain += category_domain

        if is_recent_filter:
            recent_ids = self._get_recently_viewed_product_ids()
            if recent_ids:
                domain = ['&'] + domain + [('id', 'in', recent_ids)]
            else:
                domain.append(('id', 'in', []))

        return domain

    def _shop_lookup_products(self, attrib_set, options, post, search, website):
        """Extend product lookup with category and recently viewed filters.

        :param attrib_set: Attributes set
        :param options: Search options dictionary
        :param post: Request POST/GET arguments
        :param search: Search term
        :param website: Current website record
        :return: Tuple of (fuzzy_search_term, product_count, products_recordset)
        """
        fuzzy, count, products = super()._shop_lookup_products(
            attrib_set, options, post, search, website
        )

        domain = [('id', 'in', products.ids)] if products else []

        selected_category_ids = [
            int(x) for x in request.httprequest.args.getlist('category_ids[]') if x.isdigit()
        ]
        if selected_category_ids:
            domain.append(('public_categ_ids', 'in', selected_category_ids))

        is_recent_filter = request.httprequest.args.get('recent') == '1'
        if is_recent_filter:
            recent_ids = self._get_recently_viewed_product_ids()
            if recent_ids:
                domain.append(('id', 'in', recent_ids))
            else:
                return fuzzy, 0, request.env['product.template']

        products = request.env['product.template'].sudo().search(
            domain, limit=options.get('ppg')
        )
        count = len(products)

        return fuzzy, count, products

    def _get_additional_shop_values(self, values):
        """Inject category filters and recently viewed products into template values.

        :param values: Base dictionary of shop values
        :return: Updated values dictionary
        """
        values = super()._get_additional_shop_values(values)

        selected_category_ids = [
            int(x) for x in request.httprequest.args.getlist('category_ids[]') if x.isdigit()
        ]
        is_recent_filter = request.httprequest.args.get('recent') == '1'

        all_categories = request.env['product.public.category'].sudo().search([], order='name ASC')
        recent_ids = self._get_recently_viewed_product_ids()

        values.update({
            'is_recent_filter': is_recent_filter,
            'selected_category_ids_all': selected_category_ids,
            'all_categories': all_categories,
            'recently_viewed_products': request.env['product.template'].sudo().browse(recent_ids),
            'has_recently_viewed': bool(recent_ids),
            'show_lookup_products': True,
        })
        return values

    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        """Update session with viewed product and render product detail page.

        :param product: product.template record
        :param category: Category string or record
        :param search: Search query string
        :param kwargs: Additional query parameters
        :return: Rendered product template response
        """
        self._update_recently_viewed_products(product.id)
        return super(MyWebsiteSale, self).product(product=product, category=category, search=search, **kwargs)


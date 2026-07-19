# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
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
###############################################################################
from datetime import datetime
import itertools
from odoo.addons.website_sale.const import SHOP_PATH
from odoo.addons.website_sale.controllers.main import WebsiteSale
from werkzeug.exceptions import NotFound
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo import fields
from odoo.http import route, request
from odoo.tools import float_round, lazy, SQL
from odoo.tools.translate import LazyTranslate, _
from odoo.fields import Command, Domain
from odoo.addons.website_sale.models.website import (
    PRICELIST_SELECTED_SESSION_CACHE_KEY,
    PRICELIST_SESSION_CACHE_KEY,
)
from ast import literal_eval

_lt = LazyTranslate(__name__)

class ProductVisibilityCon(WebsiteSale):

    def sitemap_shop(env, rule, qs):
        website = env['website'].get_current_website()
        if website and website.ecommerce_access == 'logged_in' and not qs:
            return

        if not qs or qs.lower() in SHOP_PATH:
            yield {'loc': SHOP_PATH}

        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, f'{SHOP_PATH}/category', Category._rec_name)
        dom &= website.website_domain()
        for cat in Category.search(dom):
            loc = f'{SHOP_PATH}/category/{env["ir.http"]._slug(cat)}'
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    def _shop_lookup_products(self, options, post, search, website):
        user = request.env.user
        product_count, details, fuzzy_search_term = website._search_with_fuzzy(
            "products_only",
            search,
            limit=None,
            order=self._get_search_order(post),
            options=options,
        )
        search_result = details[0].get('results', request.env['product.template']).with_context(bin_size=True)

        if user.has_group('base.group_portal'):
            portal_visibility = request.env['ir.config_parameter'].sudo().get_param('is_product_visibility_portal_user')
            filter_mode_portal = request.env['ir.config_parameter'].sudo().get_param('filter_mode_portal')
            if portal_visibility:
                if filter_mode_portal == "product_only":
                    portal_products = literal_eval(
                        request.env['ir.config_parameter'].sudo().get_param(
                            'website_product_visibility.available_products_for_portal_ids', '[]'
                        )
                    )
                    search_result &= request.env['product.template'].browse(portal_products)
                elif filter_mode_portal == "categ_only":
                    portal_cats = literal_eval(
                        request.env['ir.config_parameter'].sudo().get_param(
                            'website_product_visibility.available_cat_for_portal_ids', '[]'
                        )
                    )
                    search_result &= request.env['product.template'].search([
                        ('public_categ_ids', 'in', portal_cats),
                        ('is_published', '=', True)
                    ])
                product_count = len(search_result)

        elif user._is_internal():
            partner = user.partner_id
            if partner.filter_mode == "product_only":
                search_result &= partner.website_available_product_ids
            elif partner.filter_mode == "categ_only":
                search_result &= request.env['product.template'].search([
                    ('public_categ_ids', 'in', partner.website_available_cat_ids.ids),
                    ('is_published', '=', True)
                ])
            if partner.filter_mode in ["product_only", "categ_only"]:
                product_count = len(search_result)

        elif user._is_public():
            guest_visibility = request.env['ir.config_parameter'].sudo().get_param('is_product_visibility_guest_user')
            filter_mode_guest = request.env['ir.config_parameter'].sudo().get_param('filter_mode')
            if guest_visibility:
                if filter_mode_guest == "product_only":
                    guest_products = literal_eval(
                        request.env['ir.config_parameter'].sudo().get_param(
                            'website_product_visibility.available_products_for_guest_ids', '[]'
                        )
                    )
                    search_result &= request.env['product.template'].browse(guest_products)
                elif filter_mode_guest == "categ_only":
                    guest_cats = literal_eval(
                        request.env['ir.config_parameter'].sudo().get_param(
                            'website_product_visibility.available_cat_for_guest_ids', '[]'
                        )
                    )
                    search_result &= request.env['product.template'].search([
                        ('public_categ_ids', 'in', guest_cats),
                        ('is_published', '=', True)
                    ])
                product_count = len(search_result)

        return fuzzy_search_term, product_count, search_result

    @route(
        [
            SHOP_PATH,
            f'{SHOP_PATH}/page/<int:page>',
            f'{SHOP_PATH}/category/<model("product.public.category"):category>',
            f'{SHOP_PATH}/category/<model("product.public.category"):category>/page/<int:page>',
        ],
        type='http',
        auth='public',
        website=True,
        list_as_website_content=_lt("Shop"),
        sitemap=sitemap_shop,
        handle_params_access_error=lambda e, **kwargs: NotFound.code,
    )
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, tags='', **post):
        if not request.website.has_ecommerce_access():
            return request.redirect(f'/web/login?redirect={request.httprequest.path}')

        is_category_in_query = category and isinstance(category, str)
        category = self._validate_and_get_category(category)
        if is_category_in_query:
            query = self._get_filtered_query_string(
                request.httprequest.query_string.decode(), keys_to_remove=['category']
            )
            return request.redirect(f'{self._get_shop_path(category, page)}?{query}', code=301)

        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0

        website = request.env['website'].get_current_website()
        website_domain = website.website_domain()
        ppg = website.shop_ppg or 21
        ppr = website.shop_ppr or 4
        gap = website.shop_gap or "16px"
        request_args = request.httprequest.args
        attribute_values = request_args.getlist('attribute_values')
        attribute_value_dict = self._get_attribute_value_dict(attribute_values)
        attribute_ids = set(attribute_value_dict.keys())
        attribute_value_ids = set(itertools.chain.from_iterable(attribute_value_dict.values()))
        if attribute_values:
            request.session['attribute_values'] = attribute_values
        else:
            request.session.pop('attribute_values', None)

        filter_by_tags_enabled = website.is_view_active('website_sale.filter_products_tags')
        if filter_by_tags_enabled:
            if tags:
                post['tags'] = tags
                tags = {self.env['ir.http']._unslug(tag)[1] for tag in tags.split(',')}
            else:
                post['tags'] = None
                tags = {}

        url = self._get_shop_path(category)
        keep = QueryURL(
            url, **self._shop_get_query_url_kwargs(search, min_price, max_price, **post)
        )

        now = datetime.timestamp(datetime.now())
        if 'website_sale_pricelist_time' in request.session:
            pricelist_save_time = request.session['website_sale_pricelist_time']
            if pricelist_save_time < now - 60 * 60:
                request.session.pop(PRICELIST_SESSION_CACHE_KEY, None)
                request.session['website_sale_pricelist_time'] = now

        filter_by_price_enabled = website.is_view_active('website_sale.filter_products_price')
        if filter_by_price_enabled:
            company_currency = website.company_id.sudo().currency_id
            conversion_rate = request.env['res.currency']._get_conversion_rate(
                company_currency, website.currency_id, request.website.company_id, fields.Date.today())
        else:
            conversion_rate = 1

        if search:
            post['search'] = search

        options = self._get_search_options(
            category=category,
            attribute_value_dict=attribute_value_dict,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            display_currency=website.currency_id,
            **post
        )
        fuzzy_search_term, product_count, search_product = self._shop_lookup_products(
            options, post, search, website
        )

        if filter_by_price_enabled:
            Product = request.env['product.template'].with_context(bin_size=True)
            search_term = fuzzy_search_term if fuzzy_search_term else search
            domain = self._get_shop_domain(search_term, category, attribute_value_dict)
            query = Product._search(domain)
            sql = query.select(
                SQL(
                    "COALESCE(MIN(list_price), 0) * %(conversion_rate)s, COALESCE(MAX(list_price), 0) * %(conversion_rate)s",
                    conversion_rate=conversion_rate,
                )
            )
            available_min_price, available_max_price = request.env.execute_query(sql)[0]

            if min_price or max_price:
                if min_price:
                    min_price = min_price if min_price <= available_max_price else available_min_price
                    post['min_price'] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price else available_max_price
                    post['max_price'] = max_price

        ProductTag = request.env['product.tag']
        if filter_by_tags_enabled and search_product:
            all_tags = ProductTag.search_fetch(Domain.AND([
                Domain('visible_to_customers', '=', True),
                Domain.OR([
                    Domain('product_template_ids.is_published', '=', True),
                    Domain('product_ids.is_published', '=', True),
                ]),
                website_domain,
            ]))
        else:
            all_tags = ProductTag

        Category = request.env['product.public.category']
        categs_domain = Domain('parent_id', '=', False) & website_domain
        if not self.env.user._is_internal():
            categs_domain &= Domain('has_published_products', '=', True)
        if search:
            search_categories = Category.search(
                Domain('product_tmpl_ids', 'in', search_product.ids) & website_domain
            ).parents_and_self
            categs_domain &= Domain('id', 'in', search_categories.ids)
        else:
            search_categories = Category

        categs = Category.search_fetch(categs_domain)
        cats = list({cat_id for pro in search_product for cat_id in pro.public_categ_ids.ids})
        search_categories = request.env['product.public.category'].search([('id', 'in', cats)])
        category_entries = search_categories
        pager = website.pager(url=url, total=product_count, page=page, step=ppg, scope=5, url_args=post)
        offset = pager['offset']
        products = search_product[offset:offset + ppg]
        products.fetch()
        variants = request.env['product.product'].sudo().browse(
            product._get_first_possible_variant_id() for product in products)
        variants.fetch()
        product_variants = dict(zip(products, variants))
        ProductAttribute = request.env['product.attribute']
        if products:
            attributes_grouped = request.env['product.template.attribute.line']._read_group(
                domain=[
                    ('product_tmpl_id', 'in', search_product.ids),
                    ('attribute_id.visibility', '=', 'visible'),
                ],
                groupby=['attribute_id'],
                order='attribute_id'
            )
            attribute_ids = [attribute.id for attribute, in attributes_grouped]
            attributes = ProductAttribute.browse(attribute_ids)
        else:
            attributes = ProductAttribute.browse(attribute_ids).sorted()

        layout_mode = 'list' if website.is_view_active('website_sale.products_list_view') else 'grid'
        products_prices = products._get_sales_prices(website)
        product_query_params = self._get_product_query_params(**post)
        grouped_attributes_values = request.env['product.attribute.value'].browse(
            attribute_value_ids
        ).sorted().grouped('attribute_id')

        values = {
            'auto_assign_ribbons': self.env['product.ribbon'].sudo().search([('assign', '!=', 'manual')]),
            'search': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
            'order': post.get('order', ''),
            'category': category,
            'attrib_values': attribute_value_dict,
            'attrib_set': attribute_value_ids,
            'pager': pager,
            'products': products,
            'product_variants': product_variants,
            'search_product': search_product,
            'search_count': product_count,
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'gap': gap,
            'categories': categs,
            'category_entries': category_entries,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'get_product_prices': lambda product: products_prices[product.id],
            'float_round': float_round,
            'shop_path': SHOP_PATH,
            'product_query_params': product_query_params,
            'grouped_attributes_values': grouped_attributes_values,
            'previewed_attribute_values': lazy(
                lambda: products._get_previewed_attribute_values(category, product_query_params),
            ),
        }
        if filter_by_price_enabled:
            values['min_price'] = min_price or available_min_price
            values['max_price'] = max_price or available_max_price
            values['available_min_price'] = float_round(available_min_price, 2)
            values['available_max_price'] = float_round(available_max_price, 2)
        if filter_by_tags_enabled:
            values.update({'all_tags': all_tags, 'tags': tags})
        if category:
            values['main_object'] = category
        values.update(self._get_additional_shop_values(values, **post))
        return request.render("website_sale.products", values)
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

import datetime
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import TableCompute, WebsiteSale
from odoo.tools import lazy


class VeloxWebsiteSale(WebsiteSale):
    """Controller extension for Velox Sports Theme."""

    def _velox_build_filtered_response(self, result, filtered_products, url, page, post):
        """
        Builds a filtered response for the shop collection pages.
        
        :param result: The original response from the shop method.
        :param filtered_products: The filtered list of product templates.
        :param url: The base URL for the collection.
        :param page: The current page number.
        :param post: Additional POST or GET parameters.
        :return: Updated response with filtered products and pagination.
        """
        if not result.qcontext:
            return result
        product_count = len(filtered_products)
        ppg = result.qcontext.get('ppg') or 20
        ppr = result.qcontext.get('ppr') or 4
        website = request.env['website'].get_current_website()
        pager = website.pager(url=url, total=product_count, page=page, step=ppg, url_args=post)
        offset = pager['offset']
        products = filtered_products[offset:offset + ppg]
        
        # map each product to its variant, and prefetch the variants (Odoo 19 pattern)
        variants = request.env['product.product'].sudo().browse(product._get_first_possible_variant_id() for product in products)
        variants.fetch()
        product_variants = dict(zip(products, variants))
        products_prices = products._get_sales_prices(website)

        result.qcontext.update({
            'search_product': filtered_products,
            'search_count': product_count,
            'pager': pager,
            'products': products,
            'product_variants': product_variants,
            'get_product_prices': lambda product: products_prices[product.id],
            'bins': lazy(lambda: TableCompute().process(products, ppg, ppr)),
        })
        if filtered_products:
            result.qcontext['attributes'] = lazy(
                lambda: request.env['product.attribute'].search([
                    ('product_tmpl_ids', 'in', filtered_products.ids),
                    ('visibility', '=', 'visible'),
                ])
            )
        return result

    def _velox_trending_template_ids(self, min_qty=5, limit=200):
        """
        Retrieves the IDs of the trending product templates based on sales volume for the current month.
        
        :param min_qty: Minimum quantity sold to be considered trending.
        :param limit: Maximum number of product variants to retrieve.
        :return: A list of product template IDs.
        """
        month_start = datetime.date.today().replace(day=1).strftime('%Y-%m-%d')
        groups = request.env['sale.order.line'].sudo()._read_group(
            domain=[
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', month_start),
                ('product_id.active', '=', True),
            ],
            groupby=['product_id'],
            aggregates=['product_uom_qty:sum'],
            order='product_uom_qty:sum desc',
            limit=limit,
        )
        variant_ids = [
            product.id for product, qty in groups
            if product and qty > min_qty
        ]
        if not variant_ids:
            return []
        variants = request.env['product.product'].sudo().browse(variant_ids)
        seen, tmpl_ids = set(), []
        for v in variants:
            tid = v.product_tmpl_id.id
            if tid not in seen:
                seen.add(tid)
                tmpl_ids.append(tid)
        return tmpl_ids

    @http.route([
        '/shop/sale', '/shop/sale/page/<int:page>',
        '/shop/new-release', '/shop/new-release/page/<int:page>',
        '/shop/trending', '/shop/trending/page/<int:page>'
    ], type='http', auth='public', website=True)
    def shop_collection(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        """
        Controller route for custom shop collections (Sale, New Release, Trending).
        
        :param page: Page number for pagination.
        :param category: Optional product category.
        :param search: Search string.
        :param min_price: Minimum price filter.
        :param max_price: Maximum price filter.
        :param ppg: Products per page.
        :param post: Additional POST or GET parameters.
        :return: Rendered response of the shop page with filtered collection.
        """
        path = request.httprequest.path
        collection = 'sale'
        if 'new-release' in path:
            collection = 'new-release'
        elif 'trending' in path:
            collection = 'trending'

        result = super().shop(page=page, category=category, search=search,
                              min_price=min_price, max_price=max_price, ppg=ppg, **post)
        all_published = result.qcontext.get('search_product')
        if all_published is None:
            return result

        filtered = all_published
        if collection == 'sale':
            sale_ribbon = request.env.ref('website_sale.sale_ribbon', raise_if_not_found=False)
            if sale_ribbon:
                filtered = all_published.filtered(lambda p: p.website_ribbon_id.id == sale_ribbon.id)
            else:
                filtered = all_published.filtered(lambda p: p.website_ribbon_id)
        elif collection == 'new-release':
            new_ribbon = request.env.ref('website_sale.new_ribbon', raise_if_not_found=False)
            if new_ribbon:
                filtered = all_published.filtered(lambda p: p.website_ribbon_id.id == new_ribbon.id)
            else:
                filtered = all_published.filtered(
                    lambda p: p.website_ribbon_id and 'new' in (p.website_ribbon_id.html or '').lower()
                )
        elif collection == 'trending':
            trending_ids = self._velox_trending_template_ids(min_qty=5, limit=500)
            if trending_ids:
                id_set = set(all_published.ids)
                ordered_ids = [tid for tid in trending_ids if tid in id_set]
                filtered = request.env['product.template'].sudo().browse(ordered_ids)
            else:
                filtered = all_published.sorted(key=lambda p: p.create_date, reverse=True)

        return self._velox_build_filtered_response(result, filtered, f'/shop/{collection}', page, post)

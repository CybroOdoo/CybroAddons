# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.tools import lazy


class WebsiteSales(WebsiteSale):
    """Display products based on selected brands."""

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):categorys>/page/<int:page>',
        '/shop/brand/<model("product.brand"):brand>',
        '/shop/brand/<model("product.brand"):brand>/page/<int:page>',
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, brand=None, products_prices=None,
             **post):

        res = super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            brand=brand,
            products_prices=products_prices,
            **post
        )

        website = request.env['website'].get_current_website()

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except (ValueError, TypeError):
                ppg = False

        if not ppg:
            ppg = website.shop_ppg or 20

        ppr = website.shop_ppr or 4

        Brand = request.env['product.brand']

        url = "/shop"

        if category:
            url = "/shop/category/%s" % request.env['ir.http']._slug(category)

        brands = Brand.search([])

        if brand:
            url = "/shop/brand/%s" % request.env['ir.http']._slug(brand)
            products_brand = request.env['product.template'].search([
                ('brand_id', '=', brand.id),
                ('sale_ok', '=', True),
                ('is_published', '=', True)
            ])

            product_brand_count = len(products_brand)

            pager_brand = request.website.pager(
                url=url,
                total=product_brand_count,
                page=page,
                step=ppg,
                scope=7,
                url_args=post
            )

            offset = pager_brand['offset']
            page_products = products_brand[offset:offset + ppg]

            products_prices = lazy(
                lambda: page_products._get_sales_prices(website)
            )

            # The template looks up each product's variant in this mapping
            variants = request.env['product.product'].sudo().browse(
                product._get_first_possible_variant_id()
                for product in page_products
            )
            variants.fetch()

            res.qcontext.update({
                'product_variants': dict(zip(page_products, variants)),
                'brand': brand,
                'pager': pager_brand,
                'products': page_products,
                'search_count': product_brand_count,
                'bins': TableCompute().process(page_products, ppg, ppr),
                'brands': brands,
                'products_prices': products_prices,
                'get_product_prices': lambda product: lazy(
                    lambda: products_prices[product.id]
                ),
            })

        else:
            res.qcontext.update({
                'brand': brand,
                'brands': brands,
            })

        return res


class ProductBrandWebsite(http.Controller):
    """Return featured product brands."""

    @http.route(
        '/product_brand',
        type='jsonrpc',
        auth='public',
        methods=['POST'],
        website=True
    )
    def featured_brands(self):
        """Fetch featured brands for the website carousel."""

        brands = request.env['product.brand'].sudo().search_read(
            [('is_featured_brand', '=', True)],
            ['name', 'id']
        )

        return brands
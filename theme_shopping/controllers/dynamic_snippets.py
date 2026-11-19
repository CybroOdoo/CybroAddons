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
#############################################################################
from odoo import http
from odoo.http import request


class DynamicSnippets(http.Controller):
    """Provide product data for the website's dynamic snippets."""
    @http.route('/top_deal_product_snippet', auth='public', type='jsonrpc',
                website=True)
    def get_best_products(self):
        """Controller to reflect chosen products in 'Top Deal'
         snippet"""
        products_search_read = request.env['product.product'].sudo().search_read(
            [('is_published', '=', True),
             ('sale_ok', '=', True),
             ('website_id', 'in', [False, request.env.website.id]),
             ('is_top_deal_product', '=', True),
             ('ready_to_top_deal', '=', True)],
            [
                'name', 'image_1920', 'website_id', 'sales_count', 'list_price',
                'actual_price', 'offer_price', 'product_tmpl_id', 'website_url',
            ],
        )
        unique_products = []
        seen_tmpl_ids = set()
        for product in products_search_read:
            if product['product_tmpl_id'][0] not in seen_tmpl_ids:
                unique_products.append(product)
                seen_tmpl_ids.add(product['product_tmpl_id'][0])
        return unique_products

    @http.route('/get_winter_product_snippet', auth='public', type='jsonrpc',
                website=True)
    def get_winter_products(self):
        """Controller to reflect chosen products in 'Winter Collection'
         snippet"""
        category = request.env.ref('theme_shopping.product_category_winter',
                                   raise_if_not_found=False)
        domain = [('is_published', '=', True),
             ('sale_ok', '=', True),
             ('website_id', 'in', [False, request.env.website.id])]
        if category:
            domain.append(('categ_id', '=', category.id))
        return request.env['product.product'].sudo().search_read(
            domain,
            [
                'name', 'image_1920', 'website_id', 'sales_count', 'list_price',
                'offer_price', 'actual_price', 'product_tmpl_id', 'website_url',
            ],
        )

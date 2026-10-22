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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Controller for getting top selling products by category."""
from odoo import http
from odoo.http import request


class TopSellingProducts(http.Controller):
    """Controller for fetching top selling products grouped by category."""

    @http.route('/top_products/categories', type='jsonrpc', auth='public', website=True)
    def products_categories(self):
        """Return top sold products, unique categories, and the current website ID."""
        current_website = request.website
        current_website_id = current_website.id if current_website else False
        domain = [('is_published', '=', True)]
        if current_website:
            domain += current_website.website_domain()
        products = request.env['product.template'].sudo().search_read(
            domain,
            fields=['name', 'public_categ_ids', 'website_id', 'sales_count'],
        )
        top_products = [p for p in products if p.get('sales_count', 0) >= 1]
        top_products.sort(
            key=lambda p: (p.get('sales_count', 0), p.get('name') or ''),
            reverse=True,
        )
        category_ids = {
            cat_id
            for prod in top_products
            for cat_id in (prod.get('public_categ_ids') or [])
        }
        category_domain = [('id', 'in', list(category_ids))]
        if current_website:
            category_domain += current_website.website_domain()
        categories = request.env['product.public.category'].sudo().search_read(
            category_domain,
            fields=['name', 'website_id', 'sequence'],
            order='sequence, name',
        )
        return top_products, categories, current_website_id

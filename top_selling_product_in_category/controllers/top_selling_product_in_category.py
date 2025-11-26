# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil (<https://www.cybrosys.com>)
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


class TopSellingProducts(http.Controller):
    """This class is for the getting top most sold products
        products_categories:
                          Function for passing top most sold products to js,
                          and it returns products, unique categories and the
                           current website
    """

    @http.route('/top_products/categories', type='json', auth='public')
    def products_categories(self):
        """Return top sold products, their unique categories, and the current website."""
        current_website = request.env['website'].sudo().get_current_website().id

        # Get all published products for the current website
        products = request.env['product.template'].with_user(
            request.env.ref('base.user_admin')).search_read(
            [('is_published', '=', True)],
            fields=['name', 'public_categ_ids', 'website_id', 'sales_count']
        )

        # Manual filtering
        products = [p for p in products if p.get('sales_count', 0) >= 1]

        # Extract all unique categories
        category_ids = {cat_id for prod in products for cat_id in
                        prod['public_categ_ids']}
        unique_categories = request.env['product.public.category'].sudo().search_read(
            [('id', 'in', list(category_ids))],
            fields=['name', 'website_id']
        )
        return products, unique_categories, current_website

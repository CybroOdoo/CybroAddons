# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class WebsiteProduct(http.Controller):
    @http.route('/get_best_sellers', auth="public", type='json', website=True)
    def get_best_sellers(self):
        """Get the top-selling products based on sales quantity."""
        query = """
            SELECT product_id, SUM(product_uom_qty) as total_qty 
            FROM sale_order_line 
            WHERE state IN ('sale', 'done')
            GROUP BY product_id 
            ORDER BY total_qty DESC 
            LIMIT 12
        """
        request.env.cr.execute(query)
        results = request.env.cr.fetchall()
        # Get product IDs from query results
        product_ids = [row[0] for row in results]
        if product_ids:
            # Fetch the corresponding product templates
            products = request.env['product.product'].sudo().browse(
                product_ids)
            best_sellers = products.mapped('product_tmpl_id')
        else:
            # Fallback to the newest products if no sales data
            best_sellers = request.env['product.template'].sudo().search([],
                                                                         limit=12)
        products_data = [{
            'name': product.name,
            'price': product.list_price,  # Website price
            'image_url': f'/web/image/product.template/{product.id}/image_1920',
            'url': f'/shop/product/{product.id}'
        } for product in best_sellers]
        values = {
            'products': products_data,
        }
        return values

    @http.route('/get_exclusive_categories', auth="public", type='json',
                website=True)
    def get_exclusive_category(self):
        """Get the selected category from theme configuration and its best-selling products"""
        # Fetch the selected category from the theme configuration
        theme_config = request.env['og.configuration'].sudo().search([],
                                                                     limit=1)
        if not theme_config or not theme_config.category_id:
            return False

        category_id = theme_config.category_id.id
        exclusive_products = request.env['product.template'].sudo().search([
            ('public_categ_ids', '=', category_id),
            ('active', '=', True)
        ], limit=9)
        products_data = [{
            'name': product.name,
            'price': product.list_price,  # Use website price
            'image_url': f'/web/image/product.template/{product.id}/image_1920',
            'url': f'/shop/product/{product.id}'
        } for product in exclusive_products]
        values = {
            'categories': products_data,
        }
        return values

    @http.route('/get_product_categories', auth="public", type='json',
                website=True)
    def get_product_category(self):
        """Get the website categories for the snippet."""
        public_categs = request.env[
            'product.public.category'].sudo().search_read(
            [('parent_id', '=', False)], fields=['name', 'image_1920', 'id']
        )
        values = {
            'categories': public_categs,
        }
        return values

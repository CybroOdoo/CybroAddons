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
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleInherit(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """Supering to update the product data."""
        res = super().shop(page, category, search, min_price, max_price, ppg,
                           **post)
        currency = request.website.currency_id
        recommended_products = self.get_personalized_recommendations()
        best_sellers = self.get_bestseller_products()
        all_products = res.qcontext.get('products', [])
        offset = int(post.get('offset', 0))
        all_product_data = [{
            'name': product.name,
            'price': product.list_price,
            'image_url': f'/web/image/product.template/{product.id}/image_1920',
            'url': f'/shop/product/{product.id}',
            'currency_symbol': currency.symbol,
            'product_id' :product.id,
            'product_variant_id':product.product_variant_id.id,
            'type':product.type,
            'products_variant_id': product.product_variant_id.id,

        } for product in all_products]
        visible_products = all_product_data[:12]

        recommended_data = [{
            'name': product.name,
            'price': product.list_price,
            'image_url': f'/web/image/product.template/{product.id}/image_1920',
            'url': f'/shop/product/{product.id}',
            'currency_symbol': currency.symbol,
            'product_id' :product.id,
            'product_variant_id':product.product_variant_id.id,
            'type':product.type,
            'products_id': product,
            'products_variant_id': product.product_variant_id.id,

        } for product in recommended_products]

        products_data = [{
            'name': product.name,
            'price': product.list_price,
            'image_url': f'/web/image/product.template/{product.id}/image_1920',
            'url': f'/shop/product/{product.id}',
            'currency_symbol': currency.symbol,
            'product_id' :product.id,
            'product_variant_id':product.product_variant_id.id,
            'type':product.type,
            'products_id': product,
            'products_variant_id': product.product_variant_id.id,

        } for product in best_sellers]

        res.qcontext.update({
            'best_sellers': products_data,
            'recommended_data': recommended_data,
            'all_products': all_product_data,
            'visible_products': visible_products,
            'total_products': len(all_product_data),
            'products_per_page': 12,
            'offset': offset + 12
        })
        return res

    def get_bestseller_products(self, **kwargs):
        """Get the top-selling products based on sales quantity."""
        query = """
            SELECT sol.product_id, SUM(sol.product_uom_qty) as total_qty 
            FROM sale_order_line sol
            JOIN product_product pp ON sol.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE sol.state IN ('sale', 'done')
            AND pt.is_published = TRUE
            GROUP BY sol.product_id 
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
            best_sellers = request.env['product.template'].sudo().search([
                ('is_published', '=', True)], limit=12)
        return best_sellers

    def get_personalized_recommendations(self):
        """Method to get personalized recommendation on the products."""
        # Get the logged-in partner
        partner = request.env.user.partner_id
        # Fetch the partner's purchase history
        orders = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['sale', 'done']),  # Only confirmed orders
        ])

        # Collect purchased product template IDs and categories
        purchased_templates = set()
        purchased_categories = set()
        for order in orders:
            for line in order.order_line:
                purchased_templates.add(
                    line.product_id.product_tmpl_id.id)
                purchased_categories.add(
                    line.product_id.categ_id.id)

        # Fetch recommended product templates based on purchase history
        recommended_templates = request.env['product.template'].search([
            ('categ_id', 'in', list(purchased_categories)),
            ('id', 'not in', list(purchased_templates)),
            ('is_published', '=', True),  # Only published products
        ], limit=10)  # Limit to 10 recommendations
        return recommended_templates

    @http.route('/shop/products/attributes', type='json', auth="public", website=True)
    def get_products_attributes(self, product_ids=None, **kw):
        """Method to get products."""
        result = {}
        if product_ids:
            products = request.env['product.template'].sudo().browse(product_ids)
            for product in products:
                result[product.id] = bool(product.valid_product_template_attribute_line_ids)
        return result

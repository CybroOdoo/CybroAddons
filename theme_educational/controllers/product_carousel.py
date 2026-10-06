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

class ProductCarousel(http.Controller):
    """Controller for fetching trending and latest products for carousel snippets."""

    @http.route(['/latest_products'], type="json", auth="public", website=True)
    def latest_products(self):
        """Fetch latest published products with vendor and pricing details.

        :return: Dictionary containing 'products' list with product data
                 including id, name, list_price, image, rating, and vendor info
        """
        domain = [('website_published', '=', True), ('sale_ok', '=', True)]
        products = request.env['product.template'].sudo().search(
            domain,
            order='create_date desc',
            limit=12
        )
        if not products:
            products = request.env['product.template'].sudo().search(
                [('website_published', '=', True)],
                order='create_date desc',
                limit=12
            )

        currency = request.website.currency_id
        result = []
        for product in products:
            vendor_name = ''
            vendor_image = False
            if product.seller_ids:
                vendor_name = product.seller_ids[0].partner_id.name
                vendor_image = product.seller_ids[0].partner_id.image_1920

            variant = product.product_variant_id or (
                product.product_variant_ids[:1] if product.product_variant_ids else False
            )
            variant_id = variant.id if variant else False

            price = currency.format(product.list_price) if currency else f"{product.list_price:.2f}"

            image_1920 = product.image_1920
            if isinstance(image_1920, bytes):
                image_1920 = image_1920.decode('utf-8')

            vendor_image_data = vendor_image
            if isinstance(vendor_image_data, bytes):
                vendor_image_data = vendor_image_data.decode('utf-8')

            result.append({
                'id': product.id,
                'product_variant_id': variant_id,
                'name': product.name,
                'list_price': product.list_price,
                'price': price,
                'image_1920': image_1920,
                'rating_last_value': product.rating_last_value or 0.0,
                'vendor_name': vendor_name,
                'vendor_image_1920': vendor_image_data,
                'url': product.website_url,
            })

        return {'products': result}

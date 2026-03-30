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

    @http.route(['/latest_products'], type="json", auth="public", website=True)
    def latest_products(self):
        """Display products in top trending product carousal"""
        products = request.env['product.template'].sudo().search(
            [('website_published', '=', True)],
            order='create_date desc',
            limit=12
        )

        result = []
        for product in products:
            vendor_name = ''
            vendor_image = False
            if product.seller_ids:
                vendor_name = product.seller_ids[0].partner_id.name
                vendor_image = product.seller_ids[0].partner_id.image_1920

            result.append({
                'id': product.id,
                'name': product.name,
                'list_price': product.list_price,
                'image_1920': product.image_1920,
                'rating_last_value': product.rating_last_value,
                'vendor_name': vendor_name,
                'vendor_image_1920': vendor_image,
                'url': product.website_url,
            })

        return {'products': result}

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ashwin T (<https://www.cybrosys.com>)
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


class PopularProductController(http.Controller):
    @http.route('/popular/products', type='json', auth='public', website=True)
    def popular_products(self):
        products = request.env['product.template'].search([
            ('is_popular', '=', True),
            ('is_published', '=', True)
        ])

        return [{
            'id': product.id,
            'name': product.name,
            'variant_count': product.popular_product_count,
            'image_url': f'/web/image/product.template/{product.id}/image_1920',
            'url': product.website_url,
        } for product in products]

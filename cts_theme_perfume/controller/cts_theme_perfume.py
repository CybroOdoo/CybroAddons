# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aswin A K(<https://www.cybrosys.com>)
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
    """For creating New routes for /get_arrival_product for rendering the
    product details from the js for the new arrival snippet"""

    @http.route('/get_arrival_product', auth="public", type='json', website=True)
    def get_arrival_product(self, **kwargs):
        """For getting the new arrival product in the
         new arrivals snippet"""
        products_count = kwargs.get('products_count', 6)
        product_ids = request.env['product.template'].sudo().search_read(
            [('website_published', '=', True)], fields=['display_name', 'list_price'],
            order='create_date desc', limit=int(products_count))
        values = {
            'products': product_ids,
        }
        return values

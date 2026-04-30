# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import http
from odoo.http import request


class WebsiteProduct(http.Controller):
    @http.route('/get_product_arrivals', auth="public", type='json', website=True)
    def get_product_arrivals(self):
        """Get the website arrival products for snippet"""
        new_arrivals = request.env['product.template'].sudo().search_read(
            [('website_published', '=', True)],
            order='create_date desc', limit=4)
        values = {
            'new_arrivals': new_arrivals,
            'symbol': request.env.user.company_id.currency_id.symbol
        }
        response = http.Response(template='theme_voltro.arrival_product_show',
                                 qcontext=values)
        return response.render()

    @http.route('/get_product_categories', auth="public", type='json', website=True)
    def get_product_category(self):
        """Get the website arrival products for snippet"""
        public_categ_id = request.env[
            'product.public.category'].sudo().search_read(
            [('parent_id', '=', False)], fields=['name', 'image_1920','id'])

        values = {
            'categories': public_categ_id,
        }
        response = http.Response(template='theme_voltro.product_categories_show',
                                 qcontext=values)
        return response.render()

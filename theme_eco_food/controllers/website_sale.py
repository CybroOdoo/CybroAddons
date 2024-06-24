# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.addons.website_sale.controllers.main import TableCompute, WebsiteSale
from odoo.tools import lazy


class EcoFoodWebsiteSale(WebsiteSale):
    """This function helps to override the functionalities of a website shop"""

    @http.route()
    def shop(self, **post):
        """this function is used to set products based on selected category on
        the category snippet option"""
        result = super().shop(**post)
        page = post.get('page', 0)
        post.pop('page', None)
        search_product = result.qcontext['search_product']
        search_product = request.env['product.template'].sudo().search([
            ('id', 'in', search_product.ids),
            ('selected_att', '=', True)
        ])
        if search_product:
            product_count = len(search_product)
            ppg = result.qcontext['ppg']
            ppr = result.qcontext['ppr']
            url = '/shop'
            website = request.env['website'].get_current_website()
            pager = website.pager(url=url, total=product_count, page=page,
                                  step=ppg, url_args=post)
            offset = pager['offset']
            products = search_product[offset:offset + ppg]
            result.qcontext['search_product'] = search_product
            result.qcontext['search_count'] = product_count
            result.qcontext['pager'] = pager
            result.qcontext['products'] = products
            result.qcontext['bins'] = lazy(
                lambda: TableCompute().process(products, ppg, ppr))
            if products:
                result.qcontext['attributes'] = lazy(
                    lambda: request.env['product.attribute'].search([
                        ('product_tmpl_ids', 'in', search_product.ids),
                        ('visibility', '=', 'visible')]))
        return result

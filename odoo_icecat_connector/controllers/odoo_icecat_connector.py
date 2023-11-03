# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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

import requests
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import QueryURL
from odoo.http import request


class Icecat(WebsiteSale):
    def _prepare_product_values(self, product, category, search, **kwargs):
        """Override method to pass the product details from the icecat to
        odoo website"""
        product_category = request.env['product.public.category']
        if category:
            category = product_category.browse(int(category)).exists()
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(attr) for attr in attribute.split("-")] for attribute in attrib_list if
                         attribute]
        attrib_set = {attribute[1] for attribute in attrib_values}
        keep = QueryURL(
            '/shop',
            **self._product_get_query_url_kwargs(
                category=category and category.id, search=search, **kwargs, ), )
        # Needed to trigger the recently viewed product rpc
        view_track = request.website.viewref("website_sale.product").track
        username = request.env['ir.config_parameter'].sudo().get_param(
            'odoo_icecat_connector.user_id_icecat')
        if username:
            response = requests.get(
                "https://live.icecat.biz/api?UserName=%s&Language=en&Content"
                "=&Brand=%s&ProductCode=%s" % (
                    str(username), product.brand, product.default_code))
            icecat = response.json()
            if 'data' in icecat:
                return {
                    'search': search,
                    'category': category,
                    'pricelist': request.website.get_current_pricelist(),
                    'attrib_values': attrib_values,
                    'attrib_set': attrib_set,
                    'keep': keep,
                    'categories': product_category.search(
                        [('parent_id', '=', False)]),
                    'main_object': product,
                    'product': product,
                    'add_qty': 1,
                    'view_track': view_track,
                    'icecat': icecat['data']
                }
            else:
                return {
                    'search': search,
                    'category': category,
                    'pricelist': request.website.get_current_pricelist(),
                    'attrib_values': attrib_values,
                    'attrib_set': attrib_set,
                    'keep': keep,
                    'categories': product_category.search(
                        [('parent_id', '=', False)]),
                    'main_object': product,
                    'product': product,
                    'add_qty': 1,
                    'view_track': view_track,
                }
        else:
            return {
                'search': search,
                'category': category,
                'pricelist': request.website.get_current_pricelist(),
                'attrib_values': attrib_values,
                'attrib_set': attrib_set,
                'keep': keep,
                'categories': product_category.search(
                    [('parent_id', '=', False)]),
                'main_object': product,
                'product': product,
                'add_qty': 1,
                'view_track': view_track,
            }

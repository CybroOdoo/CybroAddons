# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class IcecatConnector(http.Controller):
    @http.route('/get_icecat_product_details', type='json',
                auth="public")
    def get_icecat_product_details(self, product_id):
        """Returns the details of a product"""
        if product_id:
            products = request.env['product.product'].sudo().browse(
                int(product_id))
            response = requests.get(
                "https://live.icecat.biz/api?UserName=%s&Language=en&Content"
                "=&Brand=%s&ProductCode=%s" % (
                    str(request.env.company.sudo().user_id_icecat),
                    products.brand, products.default_code))
            if 'data' in response.json():
                status = True
            else:
                status = False
            return {
                'brand': products.brand,
                'product_code': products.default_code,
                'username': str(request.env.company.sudo().user_id_icecat),
                'status': status
            }

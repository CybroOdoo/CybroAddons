# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape


class ProductsController(http.Controller):

    # adding stock check option in portal
    @http.route('/my/products', type='http', auth="user", website=True)
    def portal_products(self, **kw):
        return request.render("portal_stock_check.portal_product_availability")

    # getting corresponding products
    @http.route('/product/search', type='json', auth="user", website=True)
    def search_product(self, **kw, ):
        product = kw.get('name')
        if product:
            res = request.env['product.product'].sudo().search_read(
                [('name', 'ilike', product), ('is_published', '=', True)])
            return res
        else:
            return False
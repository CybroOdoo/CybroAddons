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

from werkzeug.exceptions import NotFound
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute, WebsiteSale
from odoo import http, fields
from odoo.http import request


class ClearCart(http.Controller):

    @http.route(['/shop/clear_cart'], type='json', auth="public", methods=['POST'], website=True)
    def clear_cart(self):
        order = request.website.sale_get_order(force_create=1)
        order_line = request.env['sale.order.line'].sudo()
        line_ids = order_line.search([('order_id', '=', order.id)])
        for line in line_ids:
            line_obj = order_line.browse([int(line)])
            if line_obj:
                line_obj.unlink()


class WebsiteProduct(http.Controller):

    @http.route('/get_arrival_product', auth="public", type='json', website=True)
    def get_arrival_product(self):
        product_ids = request.env['product.template'].sudo().search([('website_published', '=', True)],
                                                                    order='create_date desc', limit=6)

        values = {'product_ids': product_ids}
        response = http.Response(template='theme_xtream.new_arrivals', qcontext=values)
        return response.render()

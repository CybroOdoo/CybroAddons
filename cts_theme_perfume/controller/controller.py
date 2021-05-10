# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class WebsiteProduct(http.Controller):

    @http.route('/get_arrival_product', auth="public", type='json', website=True)
    def get_arrival_product(self):

        product_ids = request.env['product.template'].sudo().search([('website_published', '=', True)],
                                                                    order='create_date desc', limit=6)

        values = {'product_ids': product_ids}
        response = http.Response(template='cts_theme_perfume.new_arrivals', qcontext=values)
        return response.render()


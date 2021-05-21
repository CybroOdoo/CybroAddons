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

    @http.route('/get_product_tab', auth="public", type='json', website=True)
    def get_product_tab(self):

        new_arrivals = request.env['product.template'].sudo().search([('website_published', '=', True)],
                                                                     order='create_date desc', limit=12)
        hot_deals = request.env['product.template'].sudo().search([('website_published', '=', True),
                                                                   ('hot_deals', '=', True)], limit=12)

        values = {
            'new_arrivals': new_arrivals,
            'hot_deals': hot_deals
        }
        response = http.Response(template='theme_boec.product_tab', qcontext=values)
        return response.render()

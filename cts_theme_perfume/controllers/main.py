# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul P I(<https://www.cybrosys.com>)
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

    @http.route('/get_arrival_product', auth="public", type='json',
                website=True)
    def get_arrival_product(self):
        """For getting the new arrival product in the
         new arrivals snippet"""
        product_ids = request.env['product.template'].sudo().search(
            [('website_published', '=', True)],
            order='create_date desc', limit=6)
        values = {'product_ids': product_ids.read()}
        symbol = request.env['res.currency'].browse(
            int(values['product_ids'][0]['currency_id'][0]))
        extra_details = {'symbol': str(symbol.symbol)}
        values.update(extra_details)
        return values

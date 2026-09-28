# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha (odoo@cybrosys.com)
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
###############################################################################
from odoo import http
from odoo.http import request


class WebsiteForm(http.Controller):
    @http.route(['/call_for_price/submit'], type='http', csrf=False,
                auth="public", website=True, methods=['POST'])
    def call_for_price(self, **post):
        """Function for store the call for price queries to backend"""
        vals = {
            'first_name': post.get('first_name'),
            'last_name': post.get('last_name'),
            'email': post.get('email'),
            'phone': post.get('phone'),
            'quantity': int(post.get('quantity') or 1),
            'message': post.get('message'),
        }
        if post.get('product_id'):
            vals['product_id'] = int(post.get('product_id'))
            
        record = request.env['call.price'].sudo().create(vals)
        if record:
            return request.render("website.contactus_thanks")

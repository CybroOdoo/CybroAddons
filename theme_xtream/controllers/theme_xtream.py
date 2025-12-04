# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    """ This controller method returns a JSON object that lists
        products newly arrived products.
        :return: a JSON object containing newly arrived products
        :rtype: dict """
    @http.route('/get_arrival_product', auth="public", type='jsonrpc',website=True)
    def get_arrival_product(self):
        """
        This return products based on last created and limits to 6
        """
        product_ids = request.env['product.template'].sudo().search(
            [('website_published', '=', True)],
            order='create_date desc', limit=6)
        data = []
        for p in product_ids:
                data.append({
                    'id': p.id,
                    'display_name': p.display_name,
                    'list_price': p.list_price,
                    'currency_id': {
                        'id': p.currency_id.id,
                        'symbol': p.currency_id.symbol,
                    },
                    'image_1920': p.image_1920,
                })
        return {"new_arrivals": data}

    @http.route('/get_testimonials', auth="public", type="jsonrpc",website=True)
    def get_testimonials(self):
        """
        This will return testimonials HTML from backend.
        """

        testimonial_ids = request.env['xtream.testimonials'].sudo().search_read([])
        return {"testimonials": testimonial_ids}


    @http.route('/subscribe_newsletter', auth='public', type='jsonrpc')
    def subscribe_newsletter(self, **kw):
        """
        To save email to newsletter mail list
        """
        if request.env['mailing.contact'].sudo().search([
            ("email", "=", kw.get("email")),
            ("list_ids", "in", [
                request.env.ref('mass_mailing.mailing_list_data').id])]):
            return False
        if request.env.user._is_public():
            visitor_sudo = (request.env['website.visitor'].sudo()
                            ._get_visitor_from_request())

            name = visitor_sudo.display_name if visitor_sudo else "Website Visitor"
        else:
            name = request.env.user.partner_id.name
        request.env['mailing.contact'].sudo().create({
            "name": name,
            "email": kw.get('email'),
            "list_ids": [request.env.ref('mass_mailing.mailing_list_data').id]
        })
        return True

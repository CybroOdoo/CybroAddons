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


class WebsiteProduct(http.Controller):
    """ This controller method returns a JSON object that lists
        products newly arrived products.
        :return: a JSON object containing newly arrived products
        :rtype: dict """
    @http.route('/get_arrival_product', auth="public", type='json')
    def get_arrival_product(self):
        """
        This return products based on last created and limits to 6
        """
        return http.Response(template='theme_xtream.new_arrivals_dynamic',
                             qcontext={'product_ids': request.env[
                                 'product.template'].sudo().search(
                                 [('website_published', '=', True)],
                                 order='create_date desc', limit=6)}).render()

    @http.route('/get_testimonials', auth="public", type="json")
    def get_testimonials(self):
        """
        This will return testimonials from backend.
        """
        return http.Response(template='theme_xtream.testimonial',
                             qcontext={'testimonials': request.env[
                                 'xtream.testimonials'].sudo(
                             ).search([])}).render()

    @http.route('/subscribe_newsletter', auth='public', type='json')
    def subscribe_newsletter(self, **kw):
        """
        To save email to newsletter mail list
        """
        if request.env['mailing.contact'].sudo().search([
            ("email", "=", kw.get("email")),
            ("list_ids", "in", [
                request.env.ref('mass_mailing.mailing_list_data').id])]):
            return False
        else:
            if request.env.user._is_public():
                visitor_sudo = request.env[
                    'website.visitor'].sudo()._get_visitor_from_request()
                if visitor_sudo:
                    name = visitor_sudo.display_name
                else:
                    name = "Website Visitor"
            else:
                name = request.env.user.partner_id.name
            request.env['mailing.contact'].sudo().create({
                "name": name,
                "email": kw.get('email'),
                "list_ids": [request.env.ref(
                    'mass_mailing.mailing_list_data').id]
            })
            return True

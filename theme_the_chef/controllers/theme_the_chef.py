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


class WebsiteChef(http.Controller):
    """Getting the booking details and stored on the backend"""

    @http.route('/book_now', type='http', auth="public", website=True)
    def book_now(self, **post):
        """To create the records to the model"""
        time = post.get('time').split(':')
        request.env['website.bookings'].sudo().create({
            'name': post.get('name'),
            'email': post.get('email'),
            'phone': post.get('phone'),
            'date': post.get('date'),
            'time': f"{time[0]}.{time[1]}",
            'persons': post.get('persons'),
            'notes': post.get('notes')
        })
        return request.render("theme_the_chef.website_bookings_form_success")

    @http.route('/subscribe_newsletter', auth='public', type='json')
    def subscribe_newsletter(self, **kw):
        """ To save email to newsletter mail list"""
        if request.env['mailing.contact'].sudo().search([
            ("email", "=", kw.get("email")),
            ("list_ids", "in",
             [request.env.ref('mass_mailing.mailing_list_data').id])]):
            return False
        elif request.env.user._is_public():
            visitor_sudo = (request.env['website.visitor'].sudo()
                            ._get_visitor_from_request())
            name = visitor_sudo.display_name if visitor_sudo else \
                "Website Visitor"
        else:
            name = request.env.user.partner_id.name
        res = request.env['mailing.contact'].sudo().create({
            "name": name,
            "email": kw.get('email'),
            "list_ids": [request.env.ref(
                'mass_mailing.mailing_list_data').id]
        })
        return True

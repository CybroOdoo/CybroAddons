# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#   Author: Cybrosys (<https://www.cybrosys.com>)
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
    """
    HTTP Controller class for handling requests related to the website products.
    """

    @http.route('/get_deal_of_the_week', type='jsonrpc', auth='public', website=True)
    def get_deal_of_the_week(self):
        """ Get deal of the week products """
        product_ids = request.env['product.template'].sudo().search_read([('deal_check', '=', False)], limit=9)
        return product_ids


    @http.route('/newsletter_subscription', auth='public', type='jsonrpc')
    def newsletter_subscription(self, **kw):
        """ To save email to a newsletter mail list"""
        list_id = request.env.ref('mass_mailing.mailing_list_data')
        ids = []
        if list_id:
            ids.append(list_id.id)
        if request.env['mailing.contact'].sudo().search([
            ("email", "=", kw.get("email")),
            ("list_ids", "in", ids)]):
            return False
        elif request.env.user._is_public():
            visitor_sudo = (request.env['website.visitor'].sudo()._get_visitor_from_request())
            name = visitor_sudo.display_name if visitor_sudo else \
                "Website Visitor"
        else:
            name = request.env.user.partner_id.name
        request.env['mailing.contact'].sudo().create({
            "name": name,
            "email": kw.get('email'),
            "list_ids": ids
        })
        return True

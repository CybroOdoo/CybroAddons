# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request


class CustomerContacts(http.Controller):
    """"Class to create a route to website"""

    @http.route(['/my/contacts'], type='http', auth='public', website=True)
    def view_customer(self):
        """Render the customer contact template and pass values to the
        website."""
        customer_contact = request.env['res.partner'].sudo().search(
            [('parent_id', '=', request.env.user.partner_id.id)])
        return request.render(
            'website_customer_contact.website_customer_contact',
            {'customer_contact_portal': customer_contact,
             'page_name': 'customer_contact'})

    @http.route(['/my/contacts/<int:contact>'], type='http', auth='public',
                website=True)
    def view_customer_details(self, contact):
        """Render the customer contact details template and pass values to
         the website."""
        customer_contact = request.env['res.partner'].sudo().search(
            [('parent_id', '=', request.env.user.partner_id.id),
             ('id', '=', contact)])
        return request.render(
            'website_customer_contact.website_customer_contact_detail',
            {'customer_contact_portal': customer_contact,
             'page_name': 'customer_contact_details'})

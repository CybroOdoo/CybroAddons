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


class WebsiteCustomerContact(http.Controller):
    """"Class to create a form to website"""

    @http.route('/contact_request_form', type="http", website=True,
                auth='public')
    def contact_request_form(self):
        """Render the contact request form template and pass values
         to the website."""
        return http.request.render(
            "website_customer_contact.website_customer_contact_request_form",
            {
                'country_id': request.env['res.country'].sudo().search([]),
                'state_id': request.env['res.country.state'].sudo().search([]),
            })

    @http.route('/contact_request_form/submit', type="http", website=True,
                auth='public')
    def contact_request_form_completed(self, **kw):
        """Handle the completion of the contact request form and create
         a new partner."""
        kw['parent_id'] = request.env.user.partner_id.id
        kw['website_id'] = request.env.website.id
        request.env['res.partner'].sudo().create(kw)
        return request.render(
            "website_customer_contact."
            "website_customer_contact_request_form_completed")

    @http.route('/contact_request_form/write', type="http", website=True,
                auth='public')
    def contact_request_form_edit(self, **kw):
        """Handle editing of a contact request form and update the
         corresponding partner record."""
        current_contact = request.env['res.partner'].sudo().browse(
            int(kw['id']))
        # To write new values
        current_contact.write(kw)
        customer_contact = request.env['res.partner'].sudo().search(
            [('parent_id', '=', request.env.user.partner_id.id)])
        return request.render(
            "website_customer_contact.website_customer_contact", {
                'customer_contact_portal': customer_contact,
                'page_name': 'customer_contact'})

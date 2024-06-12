# -- coding: utf-8 --
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request


class WebsiteCustomerContact(http.Controller):
    """" Class to create a form to create new contacts in website """
    @http.route('/contact_request_form', type="http", website=True,
                auth='public')
    def contact_request_form(self):
        """ Render the contact request form template and pass values
         to the website. """
        return http.request.render(
            "website_customer_contact.website_customer_contact_request_form",
            {
                'contact_title': request.env['res.partner.title']
                .sudo().search([]),
                'country_id': request.env['res.country'].sudo().search([]),
                'state_id': request.env['res.country.state'].sudo().search([]),
            })

    @http.route('/contact_request_form/submit', type="http", website=True,
                auth='public')
    def contact_request_form_completed(self, **kw):
        """ Handle the completion of the contact request form and create a
        new partner. """
        kw['parent_id'] = int(request.env.user.partner_id.id)
        kw['website_id'] = int(request.website.id)
        if kw['country_id']:
            kw['country_id'] = int(kw['country_id'])
        if kw['state_id']:
            kw['state_id'] = int(kw['state_id'])
        request.env['res.partner'].sudo().create(kw)
        return request.render(
            "website_customer_contact."
            "website_customer_contact_request_form_completed")

    @http.route('/contact_request_form/write', type="http", website=True,
                auth='public')
    def contact_request_form_edit(self, **kw):
        """ Handle editing of a contact request form and update the
         corresponding partner record. """
        current_contact = request.env['res.partner'].sudo().browse(
            int(kw['id']))
        current_contact.write(kw)
        return request.render(
            "website_customer_contact"
            ".website_customer_contact_request_form_completed", {})

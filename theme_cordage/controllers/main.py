# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: SANJAY P (odoo@cybrosys.com)
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
"""Controllers for the Theme Cordage website routes."""
from odoo import http
from odoo.http import request


class CordageThemeController(http.Controller):
    """Controller handling website route navigation and submissions for Theme Cordage."""

    @http.route('/about-us', type='http', auth='public', website=True)
    def about_page(self, **kwargs):
        """
        Handle the /about-us route by explicitly rendering the custom
        theme template.
        """
        return request.render('theme_cordage.about_template', {})

    @http.route('/industries', type='http', auth='public', website=True)
    def industries_page(self, **kwargs):
        """
        Handle the /industries route by explicitly rendering the custom
        theme template.
        """
        return request.render('theme_cordage.industries_template', {})

    @http.route(
        '/cordage/contact/submit',
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=True,
    )
    def contact_submit(self, **kwargs):
        """Receive contact form POST, create a CRM lead, and redirect."""
        fname = (kwargs.get('fname') or '').strip()
        lname = (kwargs.get('lname') or '').strip()
        email = (kwargs.get('email_from') or '').strip()
        company = (kwargs.get('partner_name') or '').strip()
        subject_sel = (kwargs.get('subject') or 'Product enquiry').strip()
        description = (kwargs.get('description') or '').strip()
        full_name = ('%s %s' % (fname, lname)).strip() or 'Website Visitor'
        # Create a CRM lead so the enquiry appears in Odoo CRM
        request.env['crm.lead'].sudo().create({
            'name': '[Contact] %s — %s' % (subject_sel, full_name),
            'contact_name': full_name,
            'email_from': email,
            'partner_name': company,
            'description': description,
            'type': 'lead',
        })
        return request.redirect('/cordage/contact/thankyou')

    @http.route('/cordage/contact/thankyou', type='http', auth='public', website=True)
    def contact_thankyou(self, **kwargs):
        """Thank-you confirmation page after form submission."""
        return request.render('theme_cordage.contactus_thankyou_template', {})

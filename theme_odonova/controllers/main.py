# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request

class OdoNovaThemeController(http.Controller):

    @http.route('/industries', type='http', auth='public', website=True)
    def industries_page(self, **kwargs):
        """
        Handle the /industries route by explicitly rendering the custom
        theme template. This avoids potential website.page DB record issues.
        """
        return request.render('theme_odonova.industries_template', {})

    @http.route('/case-studies', type='http', auth='public', website=True)
    def case_studies_page(self, **kwargs):
        """
        Handle the /case-studies route by explicitly rendering the custom
        theme template. This avoids potential website.page DB record issues.
        """
        return request.render('theme_odonova.case_studies_template', {})
    @http.route('/about_us', type='http', auth='public', website=True)
    def about_page(self, **kwargs):
        """
        Handle the /about route by explicitly rendering the custom
        theme template.
        """
        return request.render('theme_odonova.about_template', {})

    @http.route(
        '/odonova/contact/submit',
        type='http',
        auth='public',
        methods=['POST'],
        website=True,
        csrf=True,
    )
    def submit_consultation(self, **kwargs):
        fname = (kwargs.get('fname') or '').strip()
        lname = (kwargs.get('lname') or '').strip()
        email = (kwargs.get('email_from') or '').strip()
        company = (kwargs.get('partner_name') or '').strip()
        goals = (kwargs.get('description') or '').strip()

        full_name = ('%s %s' % (fname, lname)).strip() or 'Unknown'

        try:
            company_email = request.env.company.email or ''
            body = (
                '<h3>New Consultation Request</h3>'
                '<p><b>Name:</b> %s</p>'
                '<p><b>Email:</b> %s</p>'
                '<p><b>Company:</b> %s</p>'
                '<p><b>Goals:</b></p><p>%s</p>'
            ) % (full_name, email, company, goals)
            request.env['mail.mail'].sudo().create({
                'subject': 'New Consultation Request — %s' % full_name,
                'email_from': company_email or email,
                'email_to': company_email,
                'body_html': body,
            })
        except Exception:
            pass

        return request.redirect('/thankyou')

    @http.route('/thankyou', type='http', auth='public', website=True)
    def thankyou_page(self, **kwargs):
        """
        Handle the /about route by explicitly rendering the custom
        theme template.
        """
        return request.render('theme_odonova.contactus_thank_you_template', {})

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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import re
from odoo import http
from odoo.http import request

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class UniversityApplicationController(http.Controller):
    """Front-end routes powering the 'Start Your Application' flow: rendering
    the application form, receiving the submission, and showing a confirmation
    page."""

    def _application_form_values(self, **kw):
        """Build the common values (selectable options + submitted data) used
        to render the application form template."""
        return {
            'application_types': request.env['university.application.type'].sudo().search([]),
            'admission_rounds': request.env['university.admission.round'].sudo().search([]),
            'values': kw,
            'error': {},
        }

    @http.route('/apply/form', type='http', auth='public', website=True, sitemap=True)
    def application_form(self, **kw):
        """Render the public admission application form."""
        return request.render(
            'theme_university.application_form_page',
            self._application_form_values(**kw),
        )

    @http.route('/apply/submit', type='http', auth='public', website=True,
                methods=['POST'])
    def application_submit(self, **post):
        """Validate the submitted application and, if valid, create the record
        and redirect to the confirmation page; otherwise re-render the form with
        error messages and the previously entered values."""
        error = {}
        name = (post.get('name') or '').strip()
        email = (post.get('email') or '').strip()
        if not name:
            error['name'] = 'Please enter your full name.'
        if not email:
            error['email'] = 'Please enter your email address.'
        elif not EMAIL_RE.match(email):
            error['email'] = 'Please enter a valid email address.'
        if error:
            values = self._application_form_values(**post)
            values['error'] = error
            return request.render('theme_university.application_form_page', values)
        vals = {
            'name': name,
            'email': email,
            'phone': (post.get('phone') or '').strip(),
            'program': (post.get('program') or '').strip(),
            'message': (post.get('message') or '').strip(),
        }
        if post.get('application_type_id'):
            vals['application_type_id'] = int(post['application_type_id'])
        if post.get('admission_round_id'):
            vals['admission_round_id'] = int(post['admission_round_id'])
        request.env['university.application'].sudo().create(vals)
        return request.redirect('/apply/thank-you')

    @http.route('/apply/thank-you', type='http', auth='public', website=True,
                sitemap=False)
    def application_thank_you(self, **kw):
        """Render the confirmation page shown after a successful submission."""
        return request.render('theme_university.application_thank_you_page', {})

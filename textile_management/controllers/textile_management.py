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
from odoo.tools import email_normalize, plaintext2html

# Star values of the checkout feedback widget, stored on sale.order.rating
FEEDBACK_RATINGS = {'1', '2', '3', '4'}


class TextileManagement(http.Controller):
    """Textile inquiry form and checkout feedback."""

    @http.route('/textile/inquiry/form', type='http', auth='public',
                website=True, sitemap=True)
    def textile_inquiry_form(self):
        """Show the textile inquiry form."""
        return request.render('textile_management.textile_inquiry_form')

    @http.route('/textile/inquiry/form/submit', type='http', auth='public',
                methods=['POST'], website=True)
    # pylint: disable=unused-argument
    def textile_inquiry_form_submit(self, name='', email='', number='',
                                    description='', **kwargs):
        """Save the inquiry, then show the thank-you page."""
        name, email = name.strip(), email.strip()
        if not name or not email_normalize(email):
            return request.redirect('/textile/inquiry/form')
        self.env['website.inquiry'].sudo().create({
            'inquirer': name,
            'email': email,
            'phone_number': number.strip(),
            'description': plaintext2html(description.strip()),
        })
        return request.redirect('/textile/inquiry/thank-you')

    @http.route('/textile/inquiry/thank-you', type='http', auth='public',
                website=True, sitemap=False)
    def textile_inquiry_thank_you(self):
        """Confirm the inquiry was received, with the company contacts."""
        company = self.env.website.company_id
        return request.render('textile_management.thankyou_template', {
            'company_mail': company.email,
            'company_phone': company.phone,
        })

    @http.route('/customer/review/session', type='jsonrpc', auth='public',
                website=True)
    # pylint: disable=unused-argument
    def save_review(self, rating=None, comment=None, **kwargs):
        """Save the rating and comment of the checkout feedback widget on the
        cart of the visitor, while it is still a quotation."""
        order_sudo = request.cart
        if not order_sudo or order_sudo.state not in ('draft', 'sent'):
            return False
        vals = {}
        if str(rating) in FEEDBACK_RATINGS:
            vals['rating'] = str(rating)
        if comment is not None:
            vals['comment'] = str(comment).strip()[:500]
        if not vals:
            return False
        order_sudo.write(vals)
        return True

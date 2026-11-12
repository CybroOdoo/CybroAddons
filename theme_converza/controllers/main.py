# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import http
from odoo.tools import html_escape
from odoo.http import request

class ConverzaForm(http.Controller):
    @http.route('/converza/audit', type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def submit_audit(self, **post):
        e = html_escape
        message = f"First Name: {e(post.get('First Name', ''))}<br/>" \
                  f"Last Name: {e(post.get('Last Name', ''))}<br/>" \
                  f"Email: {e(post.get('Email', ''))}<br/>" \
                  f"Company: {e(post.get('Company', ''))}<br/>" \
                  f"Website: {e(post.get('Website', ''))}<br/>" \
                  f"Service Interest: {e(post.get('Service Interest', ''))}<br/>" \
                  f"Budget: {e(post.get('Budget', ''))}<br/>" \
                  f"Goals: {e(post.get('Goals', ''))}"
        
        request.env['mail.mail'].sudo().create({
            'subject': 'New Strategy Audit Request',
            'body_html': message,
            'email_to': 'hello@converza.agency',
            'email_from': post.get('Email', 'noreply@converza.agency'),
        }).send()
        
        return request.redirect('/contactus-thank-you')

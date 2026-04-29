# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
######################################################################################
from odoo import http
from odoo.http import request, route


class TextileManagement(http.Controller):
    """For textile management"""

    @http.route(['/textile/inquiry/form'], type='http', auth='public',
                website=True)
    def textile_inquiry_form(self):
        """For textile inquiry form"""
        return http.request.render(
            "textile_management.textile_inquiry_form", {})

    @route('/textile/inquiry/form/submit', type='http', auth='public',
           methods=['POST'], csrf=False, website=True)
    def textile_inquiry_form_submit(self, **kwargs):
        """For saving data to backend from website form"""
        website_inquiry = request.env['website.inquiry'].sudo().create({
            'inquirer': kwargs.get('name'),
            'email': kwargs.get('email'),
            'phone_number': kwargs.get('number'),
            'description': kwargs.get('description'),
        })
        mail_template = request.env.ref(
            'textile_management.'
            'mail_template_website_inquiry').with_context(
            inquirer=kwargs.get('name'), email=kwargs.get('email'),
            phone_number=kwargs.get('number'), description=kwargs.get(
                'description'), email_from=kwargs.get('email'),
            email_to=request.env.company.email)
        mail_template.sudo().send_mail(website_inquiry.id, force_send=True)
        response = request.render("textile_management.thankyou_template", {})
        return response


    @http.route('/customer/review/session', type='json', auth='public',
                website=True)
    def save_review(self, **kwargs):
        data = request.params or {}

        rating = data.get('rating')
        comment = data.get('comment')

        if not rating:
            return False

        request.session['checkout_feedback'] = {
            'rating': str(rating),
            'comment': comment or '',
        }

        return True

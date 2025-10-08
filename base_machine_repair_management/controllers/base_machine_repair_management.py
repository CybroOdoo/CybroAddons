"""Machine Repair management"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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


class RepairRequest(http.Controller):
    """This is used for manage the repair requests"""

    @http.route(['/repair'], type='http', auth="public", website=True)
    def get_request(self):
        """This is used to get the repair request form"""
        vals = ({
            'machine': request.env['product.product'].sudo().search(
                [('is_machine', '=', True)]),
            'service': request.env['machine.service'].sudo().search([]),
            'customer_id': request.env['res.partner'].search(
                []),
        })
        return request.render(
            "base_machine_repair_management.repair_request_form", vals)

    @http.route('/create/repair_request', methods=['POST', 'GET'], type='http',
                auth="public", website=True, csrf=False)
    def submit_form_request(self, **POST):
        """This is used to redirect the submitted response page"""
        if POST.get('customer_id') not in request.env[
            'res.partner'].sudo().search([]).ids:
            customer = request.env['res.partner'].sudo().create({
                'name': POST.get('customer_id'),
                'email': POST.get('email'),
                'phone': POST.get('phone')
            })
        POST.update({'customer_id': customer.id, 'name': 'Repair from Website'})
        if POST:
            request.env['machine.repair'].sudo().create(POST)
            return request.redirect('/contactus-thank-you')

    @http.route(['/review'], type='http', auth="public", website=True)
    def get_customer_review(self):
        """This is used to redirect the review form"""
        comments = ({
            'customer_rating': request.env['machine.repair'].search(
                [('customer_id', '!=', False), ('customer_rating', '!=', False),
                 ('customer_comments', '!=', False)])
        })
        return request.render(
            "base_machine_repair_management.repair_review_form", comments)

    @http.route('/create/repair_reviews', methods=['POST', 'GET'], type='http',
                auth="public", website=True, csrf=False)
    def submit_form(self, **POST):
        """This is used to submit the user reviews"""
        user = request.env.user.name
        if POST:
            vals = request.env['machine.repair'].sudo().search(
                [('customer_id', '=', user)])
            if POST.get('good') == 'on':
                vals.write({
                    'customer_rating': 'Good',
                    'customer_comments': POST['repair_review_comment']
                })
            elif POST.get('poor') == 'on':
                vals.write({
                    'customer_rating': 'Poor',
                    'customer_comments': POST['repair_review_comment']
                })
            elif POST.get('average') == 'on':
                vals.write({
                    'customer_rating': 'Average',
                    'customer_comments': POST['repair_review_comment']
                })
            elif POST.get('excellent') == 'on':
                vals.sudo().write({
                    'customer_rating': 'Excellent',
                    'customer_comments': POST['repair_review_comment']
                })
            return request.redirect('/contactus-thank-you')

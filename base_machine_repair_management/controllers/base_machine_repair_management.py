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
import base64

from odoo import http
from odoo.http import request


REPAIR_FORM_FIELDS = (
    'repairing_reason', 'machine_id', 'machine_brand', 'manufacturing_year',
    'service_id', 'machine_model', 'priority', 'repair_detail', 'damage',
)


class RepairRequest(http.Controller):
    """Controller to manage the website repair requests."""

    @http.route(['/repair'], type='http', auth="public", website=True)
    def get_request(self):
        """Render the repair request form."""
        vals = ({
            'machine': request.env['product.product'].sudo().search(
                [('is_machine', '=', True)]),
            'service_id': request.env['machine.service'].sudo().search([]),
            'customer_id': request.env['res.partner'].search([]),})
        return request.render(
            "base_machine_repair_management.repair_request_form", vals)

    @http.route('/create/repair_request', type='http', methods=['POST'],
                auth="public", website=True)
    def submit_form_request(self, **POST):
        """Create a repair request from the submitted website form."""
        user = request.env.user
        if user._is_public():
            name = (POST.get('customer_id') or '').strip()
            if not name:
                return request.redirect('/repair')
            customer = request.env['res.partner'].sudo().create({
                'name': name,
                'email': POST.get('customer_email'),
                'phone': POST.get('phone'),
            })
        else:
            customer = user.partner_id
        vals = {field: POST[field] for field in REPAIR_FORM_FIELDS
                if POST.get(field)}
        vals.update({'customer_id': customer.id, 'name': 'Repair from Website'})
        files = [f for f in request.httprequest.files.getlist('repair_images')
                 if f and f.filename and (f.mimetype or '').startswith('image/')]
        for i, f in enumerate(files[:5], start=1):
            vals['image%s' % i] = base64.b64encode(f.read()).decode()
        request.env['machine.repair'].sudo().create(vals)
        return request.redirect('/contactus-thank-you')

    @http.route(['/review'], type='http', auth="public", website=True)
    def get_customer_review(self):
        """Render the customer review form."""
        comments = ({
            'customer_rating': request.env['machine.repair'].sudo().search(
                [('customer_id', '!=', False), ('customer_rating', '!=', False),
                 ('customer_comments', '!=', False)])
        })
        return request.render(
            "base_machine_repair_management.repair_review_form", comments)

    @http.route('/create/repair_reviews', methods=['POST'], type='http',
                auth="user", website=True)
    def submit_form(self, **POST):
        """Save the review submitted by the customer."""
        ratings = {'poor': 'Poor', 'average': 'Average', 'good': 'Good',
                   'excellent': 'Excellent'}
        rating = ratings.get(POST.get('rating'))
        comment = POST.get('repair_review_comment')
        if rating and comment:
            repair = request.env['machine.repair'].sudo().search(
                [('customer_id', '=', request.env.user.partner_id.id)],
                limit=1)
            repair.write({
                'customer_rating': rating,
                'customer_comments': comment,
            })
        return request.redirect('/contactus-thank-you')

# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError


class WebsiteTestimonialController(http.Controller):
    @http.route('/website/testimonials/fetch', type='jsonrpc', auth='public', website=True)
    def fetch_testimonials(self):
        return request.env['website.testimonial'].sudo().search_read(
            [], fields=['user_id', 'testimonial', 'image'])

    @http.route('/fetch_user_group', type='jsonrpc', auth='public', website=True)
    def check_user_group(self, **kwargs):
        user = request.env.user
        return not user._is_public() and (
            user.has_group('theme_shopping.testimonial_user')
            or user.has_group('website.group_website_designer'))

    @http.route('/website/testimonial/create', type='jsonrpc', auth='user', website=True)
    def create_testimonial(self, testimonial, **kwargs):
        if not self.check_user_group():
            raise AccessError(request.env._('You cannot submit testimonials.'))
        if not isinstance(testimonial, str) or not testimonial.strip():
            raise ValidationError(request.env._('Please enter a testimonial.'))
        user = request.env.user
        request.env['website.testimonial'].sudo().create({
            'user_id': user.id,
            'testimonial': testimonial.strip(),
            'image': user.image_1920,
        })
        return {'status': 'success'}

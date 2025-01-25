# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.http import request


class WebsiteTestimonialController(http.Controller):
    @http.route('/website/testimonials/fetch', type='json', auth='public')
    def fetch_testimonials(self):
        """Fetch all testimonials"""
        try:
            testimonials = request.env['website.testimonial'].sudo().search([])
            return [{
                'user_name': testimonial.user_id.name,
                'testimonial': testimonial.testimonial,
                'image': testimonial.image,
            } for testimonial in testimonials]
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    @http.route('/fetch_user_group', type='json', auth='public', methods=['POST'])
    def check_user_group(self, userId, **kwargs):
        """Check the user group of current logged-in user"""
        user_group = request.env['res.users'].search([('id', '=', userId)])
        user_has_group = (
            user_group.has_group('theme_shopping.testimonial_user') or
            user_group.has_group('website.group_website_designer')
        )
        return user_has_group

    @http.route('/website/testimonial/create', type='json', auth='public', methods=['POST'])
    def create_testimonial(self, testimonial, **kwargs):
        """Create a new testimonial record"""
        try:
            current_user = request.env.user
            user_name = current_user.id
            user_image = current_user.image_1920
            request.env['website.testimonial'].sudo().create({
                'user_id': user_name,
                'testimonial': testimonial,
                'image': user_image,
            })
            return {'status': 'success'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
#
################################################################################
from odoo import http
from odoo.http import request


class DashboardCarousel(http.Controller):

    @http.route('/get_dashboard_carousel', auth="public", type='jsonrpc')
    def get_dashboard_carousel(self):
        """Returns Instagram posts data as JSON array"""
        posts = request.env['insta.post'].sudo().search([], limit=12, order='create_date desc')

        result = []
        for post in posts:
            result.append({
                'id': post.id,
                'caption': post.caption or '',
                'has_image': bool(post.post_image),  # Flag to check if image exists
                'profile_username': post.profile_id.username if post.profile_id else 'instagram'
            })
        return result

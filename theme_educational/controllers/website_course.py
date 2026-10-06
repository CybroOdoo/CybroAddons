# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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


class WebsiteCourses(http.Controller):
    """Controller for rendering popular courses and tag filtering on homepage."""

    @http.route(['/'], type='http', auth="public", website=True)
    def popular_courses(self, **kwargs):
        """Display popular courses and course tags on the website homepage.

        :param kwargs: Additional query parameters
        :return: HTTP response rendering 'website.homepage' template
        """
        courses = request.env['slide.channel'].sudo().search([], limit=50)
        course_tags = request.env['slide.channel.tag'].sudo().search([])

        return request.render('website.homepage', {
            'courses': courses,
            'course_tags': course_tags,
            'active_tag': None,
        })

    @http.route(['/popular_courses/filter'], type='json', auth="public", website=True)
    def filter_courses(self, tag_id=None):
        """Filter popular courses dynamically by course tag.

        :param tag_id: Integer ID of the slide.channel.tag to filter by
        :return: HTML string rendered from 'theme_educational.popular_courses_cards'
        """
        domain = []
        if tag_id:
            domain = [('tag_ids', 'in', [int(tag_id)])]
        courses = request.env['slide.channel'].sudo().search(domain, limit=50)
        return request.env['ir.ui.view']._render_template(
            'theme_educational.popular_courses_cards',
            {'courses': courses}
        )

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class College(http.Controller):
    """Class used to define function which renders appropriate template."""

    @http.route('/college_alumni', type='http', website=True, auth='public')
    def college_alumni(self):
        """Renders template college_alumni."""
        return http.request.render('theme_college.college_alumni', {})

    @http.route('/college_course', type='http', website=True, auth='public')
    def college_course(self):
        """Renders template college_course."""
        return http.request.render('theme_college.college_course', {})

    @http.route('/college_facility', type='http', website=True, auth='public')
    def college_facility(self):
        """Renders template college_facility."""
        return http.request.render('theme_college.college_facility', {})

    @http.route('/college_gallery', type='http', website=True, auth='public')
    def college_gallery(self):
        """Renders template college_gallery."""
        return http.request.render('theme_college.college_gallery', {})

    @http.route('/get_college_locations', auth="public", type='json',
                website=True)
    def get_college_location(self):
        """Function to search all college locations and pass values."""
        college_location = request.env['college.location'].sudo().search([],
                                                                         order='create_date desc')
        values = {
            'college_location': college_location,
        }
        response = http.Response(template='theme_college.college_locations',
                                 qcontext=values)
        return response.render()

    @http.route('/college_location/<int:college_location_id>', type='http',
                auth='public',
                website=True)
    def view_country_details(self, college_location_id):
        """Function to render template and pass value to website."""
        college_location = request.env['college.location'].sudo().browse(college_location_id)
        values = {
            'college_location': college_location
        }
        return request.render(
            'theme_college.college_location_country', values)

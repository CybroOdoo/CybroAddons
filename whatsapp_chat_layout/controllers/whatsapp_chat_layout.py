# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
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


class Color(http.Controller):
    """The ProjectFilter class provides the filter option to the js.
    When applying the filter returns the corresponding data."""

    @http.route('/select_color', auth='public', type='json')
    def get_color(self):
        """Function to return values into js"""
        colors = {'background_color': request.env[
            'ir.config_parameter'].sudo().get_param(
            'base_setup.background_color'), 'layout_color': request.env[
            'ir.config_parameter'].sudo().get_param(
            'base_setup.layout_color'),
            'background_image': request.env.user.company_id.background_image}
        return colors

    @http.route('/select_user_image', auth='public', type='json')
    def get_user_image(self):
        """function to get current user image and return in js"""
        return request.env.user.partner_id.image_1920

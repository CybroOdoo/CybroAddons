# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana J(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Mandatory field values"""
from odoo import http
from odoo.http import request


class MandatoryFieldSettings(http.Controller):
    """Controller to return the method of values from config settings."""
    @http.route('/mandatory/config_params', type='json', auth="public")
    def website_get_config_value(self):
        """Returning the values from config settings to js"""
        get_param = request.env['ir.config_parameter'].sudo().get_param
        return {
            'margin_left_color': get_param(
                'mandatory_field_highlight.margin_left_color'),
            'margin_right_color': get_param(
                'mandatory_field_highlight.margin_right_color'),
            'margin_top_color': get_param(
                'mandatory_field_highlight.margin_top_color'),
            'margin_bottom_color': get_param(
                'mandatory_field_highlight.margin_bottom_color'),
            'field_background_color': get_param('mandatory_field_highlight'
                                                '.field_background_color')
        }

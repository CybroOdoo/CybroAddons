# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
from odoo.addons.web.controllers import home


class GoogleAnalytics(home.Home):
    """This class is inheriting the controller web and add a
       Method
       Methods:
           google_analytics():
               Returns the Measurement id and api secret"""

    @http.route('/analytics', type="json", auth="public")
    def google_analytics(self):
        """Returns the Measurement id and api secret"""
        return {
            'measurement_id': request.env[
                'ir.config_parameter'].sudo().get_param(
                'google_analytics_odoo.measurement_id_analytics'),
            'api_secret': request.env['ir.config_parameter'].sudo().get_param(
                'google_analytics_odoo.api_secret'),
            'enable_analytics': request.env[
                'ir.config_parameter'].sudo().get_param(
                'google_analytics_odoo.enable_analytics'),
        }


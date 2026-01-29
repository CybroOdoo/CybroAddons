# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
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
###############################################################################
import requests
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Add field to configuration settings"""
    _inherit = 'res.config.settings'

    google_search = fields.Boolean(
        string='Allow the users to synchronize the google search',
        config_parameter='google_search_in_odoo.enable_google_search',
        help="For synchronizing the google search")
    ser_client_api = fields.Char(
        "API Key",
        config_parameter='google_search_in_odoo.ser_client_api',
        help="Google search api key")
    ser_client_engine = fields.Char(
        "Search Engine",
        config_parameter='google_search_in_odoo.ser_client_engine',
        help="Search engine ID")

    @api.model
    def google_search_config(self, input_data):
        """Create function to get google custom search api response"""
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'google_search_in_odoo.ser_client_api')
        search_engine = self.env['ir.config_parameter'].sudo().get_param(
            'google_search_in_odoo.ser_client_engine')
        google_search = self.env['ir.config_parameter'].sudo().get_param(
            'google_search_in_odoo.enable_google_search')
        if not google_search:
            return {
                'error': 'Please Enable Google Search.'
            }
        else:
            if not api_key and not search_engine:
                return {
                    'error': 'Please provide API key and Search engine ID.'
                }
            base_url = 'https://www.googleapis.com/customsearch/v1'
            params = {
                'q': input_data,
                'key': api_key,
                'cx': search_engine,
                'num': 10,
            }
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                return items

# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
import requests
from itertools import chain
from odoo import api, fields, models

USER_PRIVATE_FIELDS = ['password']
concat = chain.from_iterable


class ResUsers(models.Model):
    """Inherits ResUsers to create records inside LoginLog"""
    _inherit = 'res.users'

    @api.model
    def _check_credentials(self, password, user_agent_env):
        """Supering the function and _check_credentials to create record
        inside LoginLog"""
        result = super()._check_credentials(password, user_agent_env)
        have_api_key = self.env['ir.config_parameter'].sudo().get_param(
            'export_delete_login_log.have_api_key')
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'export_delete_login_log.ipapi_key')
        ip_address = (requests.get(
            f'https://api.ipify.org?format=json').json()).get('ip')
        response = requests.get(
            f"https://ipapi.co/{ip_address}/json/?key={api_key}").json()\
            if have_api_key else requests.get(
            f"https://ipapi.co/{ip_address}/json/").json()
        geo_loc = False
        if response.get('latitude') and response.get('longitude'):
            geo_loc = f"{response.get('latitude')}, {response.get('longitude')}"

        address = False
        address_parts = [response.get('city'), response.get('region'), response.get('country_name')]
        if any(address_parts):
            address = ", ".join(filter(None, address_parts))

        self.env['login.log'].sudo().create(
            {'name': self.name,
             'ip_address': ip_address,
             'geo_loc': geo_loc,
             'address': address,
             'postal_code': response.get("postal"),
             'time_zone': response.get("timezone"),
             'remark': ("Free quota exceeded"
                        if response.get("reason") == "RateLimited"
                        else response.get("reason")) if response.get("error") else None
             })
        return result


class LoginLog(models.Model):
    """Model to log information about user login"""
    _name = 'login.log'
    _description = 'Login Log'

    name = fields.Char(string="User Name", readonly=True)
    date_time = fields.Datetime(string="Login Date And Time",
                                default=lambda self: fields.datetime.now(),
                                readonly=True)
    ip_address = fields.Char(string="IP Address", readonly=True)
    geo_loc = fields.Char(string="Latitude / Longitude", readonly=True,
                          help="Data is fetched using users IP address so the "
                               "it may not be 100% precise")
    address = fields.Char(string="Address", readonly=True,
                          help="Data is fetched using users IP address so the "
                               "it may not be 100% precise")
    postal_code = fields.Char(string="Postal Code", readonly=True,
                              help="Data is fetched using users IP address so "
                                   "the it may not be 100% precise")
    time_zone = fields.Char(string="Time Zone", readonly=True,
                            help="Data is fetched using users IP address so "
                                 "the it may not be 100% precise")
    remark = fields.Text(string="Remarks",
                         help="Remark is added when there is an error in the "
                              "IP Address or other values, Error Reason: "
                              "\n1) RateLimited: Free daily quota exceeded"
                              "\n2) Invalid IP Address: The IP address used "
                              "by the User is Invalid"
                              "\n3) Reserved IP Address: The IP address used "
                              "by the User is Reserved")

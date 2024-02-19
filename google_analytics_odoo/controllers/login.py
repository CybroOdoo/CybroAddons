# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import requests
from odoo.addons.web.controllers.home import Home
from odoo.http import request


class Login(Home):
    """Extends the functionality of the web login process by adding
      additional analytics tracking upon successful login."""
    def web_login(self, redirect=None, **kw):
        """Controller for the web login process.
           :param redirect: URL to redirect after login.
           :param kw: Additional keyword arguments.
           :return: Result of the web login process."""
        res = super().web_login(redirect=None, **kw)
        login_success = request.params['login_success']
        if login_success:
            enable_analytics = request.env[
                'ir.config_parameter'].sudo().get_param(
                'google_analytics_odoo.enable_analytics'),
            measurement_id = request.env[
                'ir.config_parameter'].sudo().get_param(
                'google_analytics_odoo.measurement_id_analytics')
            api_secret = request.env['ir.config_parameter'].sudo().get_param(
                'google_analytics_odoo.api_secret')
            if enable_analytics:
                url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
                data = {
                    "client_id": str(request.env.user.id),
                    "events": [{
                        "name": "Login_Information",
                        "params": {
                            "User_login": kw['login'],
                            "Name": request.env.user.name,
                            "Email": request.env.user.partner_id.email,
                        }
                    }]
                }
                requests.post(url, json=data)
        return res

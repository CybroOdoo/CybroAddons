# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import logging
import requests
from odoo import http
from odoo.addons.web.controllers.home import Home
from odoo.http import request

_logger = logging.getLogger(__name__)


class Login(Home):
    """Extends the functionality of the web login process by adding
      additional analytics tracking upon successful login."""

    @http.route('/web/login', type='http', auth='public', website=True, sitemap=False)
    def web_login(self, *args, **kw):
        """Controller for the web login process.
           :param args: Positional arguments.
           :param kw: Additional keyword arguments.
           :return: Result of the web login process."""
        res = super().web_login(*args, **kw)
        login_success = request.params.get('login_success')
        if login_success:
            try:
                enable_analytics = request.env[
                    'ir.config_parameter'].sudo().get_str(
                    'google_analytics_odoo.enable_analytics'
                )
                measurement_id = request.env[
                    'ir.config_parameter'].sudo().get_str(
                    'google_analytics_odoo.measurement_id_analytics'
                )
                api_secret = request.env['ir.config_parameter'].sudo().get_str(
                    'google_analytics_odoo.api_secret'
                )
                if enable_analytics and measurement_id and api_secret:
                    url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
                    data = {
                        "client_id": str(request.env.user.id),
                        "events": [{
                            "name": "Login_Information",
                            "params": {
                                "User_login": kw.get('login') or request.params.get('login') or request.env.user.login,
                                "Name": request.env.user.name,
                                "Email": request.env.user.partner_id.email or '',
                            }
                        }]
                    }
                    requests.post(url, json=data, timeout=5)
            except Exception as e:
                _logger.warning("Google Analytics Login tracking error: %s", e)
        return res

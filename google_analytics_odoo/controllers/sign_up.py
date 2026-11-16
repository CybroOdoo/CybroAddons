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
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as signup
from odoo.http import request

_logger = logging.getLogger(__name__)


class AnalyticsSignUp(signup):
    """
       Extends the functionality of user signup process by adding
       additional analytics tracking upon successful signup.
    """

    def _signup_with_values(self, token, values, do_login):
        """Handle user signup and report the signup event to Google Analytics."""
        result = super()._signup_with_values(token, values, do_login)
        try:
            enable_analytics = request.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.enable_analytics'
            )
            measurement_id = request.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.measurement_id_analytics'
            )
            api_secret = request.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.api_secret'
            )

            if enable_analytics and measurement_id and api_secret:
                url = (
                    f"https://www.google-analytics.com/mp/collect"
                    f"?measurement_id={measurement_id}&api_secret={api_secret}"
                )
                data = {
                    "client_id": str(request.session.uid),
                    "events": [{
                        "name": "Signup_Information",
                        "params": {
                            "User_login": request.env.user.login,
                            "Name": request.env.user.name,
                            "Email": request.env.user.partner_id.email or '',
                        }
                    }]
                }
                requests.post(url, json=data, timeout=5)
        except Exception as e:
            _logger.warning("Google Analytics Signup_Information error: %s", e)
        return result

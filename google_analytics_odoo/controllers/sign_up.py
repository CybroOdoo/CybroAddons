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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""This module extends the signup process to track analytics."""
import requests
from odoo import _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as signup
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.http import request


class AnalyticsSignUp(signup):
    """
       Extends the functionality of user signup process by adding
       additional analytics tracking upon successful signup.
       """
    def _signup_with_values(self, token, values):
        """Creates a new user account with the provided values and token.
            :param token: Token for user signup.
            :param values: Dictionary of user data.
            :raises SignupError: If authentication fails."""
        login, password = request.env['res.users'].sudo().signup(values, token)
        # as authenticate will use its own cursor we need to commit the current transaction
        request.env.cr.commit()
        credential = {'login': login, 'password': password, 'type': 'password'}
        pre_uid = request.session.authenticate(request.db, credential)
        if not pre_uid:
            raise SignupError(_('Authentication Failed.'))
        enable_analytics = request.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.enable_analytics')
        measurement_id = request.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.measurement_id_analytics')
        api_secret = request.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.api_secret')
        if enable_analytics:
            url = (
                f"https://www.google-analytics.com/mp/collect?"
                f"measurement_id={measurement_id}&api_secret={api_secret}"
            )
            data = {
                "client_id": str(pre_uid),
                "events": [{
                    "name": "Signup_Information",
                    "params": {
                        "User_login": login,
                        "Name": request.env.user.name,
                        "Email": request.env.user.partner_id.email,
                    }
                }]
            }
            requests.post(url, json=data)

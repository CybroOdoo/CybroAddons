# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import secrets
from datetime import timedelta
import requests
from odoo import fields, models
from odoo.exceptions import ValidationError, UserError

TIMEOUT = 20


class ResCompany(models.Model):
    """ Inherit the company form view"""
    _inherit = "res.company"

    hangout_client_id = fields.Char(
        "Client ID", groups='base.group_system',
        help='Google Cloud Console OAuth Client ID')
    hangout_client_secret = fields.Char(
        "Client Secret", groups='base.group_system',
        help='Google Cloud Console OAuth Client Secret')
    hangout_redirect_uri = fields.Char(
        "Authorized redirect URIs", groups='base.group_system',
        help='Google authorized redirect URIs')
    hangout_company_access_token = fields.Char(
        'Access Token', copy=False, groups='base.group_system',
        help="Google Meet access token")
    hangout_company_access_token_expiry = fields.Datetime(
        string='Token expiry', copy=False, groups='base.group_system',
        help="Google Meet access token expiry date")
    hangout_company_refresh_token = fields.Char(
        'Refresh Token', copy=False, groups='base.group_system',
        help="Google Meet refresh token")
    hangout_company_authorization_code = fields.Char(
        string="Authorization Code", copy=False, groups='base.group_system',
        help="Google Meet authorization code")
    hangout_oauth_state = fields.Char(
        string="OAuth State", copy=False, groups='base.group_system',
        help="One-time value sent to Google with the authorization request "
             "and checked when Google redirects back to Odoo.")

    def action_google_meet_company_authenticate(self):
        """Method for authentication"""
        if not self.hangout_client_id:
            raise ValidationError(self.env._("Please enter the Client ID."))
        client_id = self.hangout_client_id
        if not self.hangout_redirect_uri:
            raise ValidationError(
                self.env._("Please enter the Authorized redirect URI."))
        redirect_url = self.hangout_redirect_uri
        state = secrets.token_urlsafe(32)
        self.hangout_oauth_state = state
        calendar_scope = 'https://www.googleapis.com/auth/calendar'
        calendar_event_scope = 'https://www.googleapis.com/auth/calendar.events'
        url = (
            "https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
            "&access_type=offline&client_id={}&redirect_uri={}&scope={}+{}"
            "&state={}"
        ).format(client_id, redirect_url, calendar_scope,
                 calendar_event_scope, state)
        return {
            "type": 'ir.actions.act_url',
            "url": url,
            "target": "new"
        }

    def action_google_meet_company_refresh_token(self):
        """Method to get the refresh token"""
        if not self.hangout_client_id:
            raise UserError(
                self.env._('Client ID is not yet configured.'))
        client_id = self.hangout_client_id

        if not self.hangout_client_secret:
            raise UserError(
                self.env._('Client Secret is not yet configured.'))
        client_secret = self.hangout_client_secret
        if not self.hangout_company_refresh_token:
            raise UserError(
                self.env._('Refresh Token is not yet configured.'))
        refresh_token = self.hangout_company_refresh_token
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }
        response = requests.post(
            'https://accounts.google.com/o/oauth2/token', data=data,
            headers={
                'content-type': 'application/x-www-form-urlencoded'},
            timeout=TIMEOUT)
        result = response.json()
        if result and result.get('access_token'):
            vals = {'hangout_company_access_token': result['access_token']}
            if result.get('expires_in'):
                vals['hangout_company_access_token_expiry'] = (
                    fields.Datetime.now()
                    + timedelta(seconds=result['expires_in']))
            self.write(vals)
        else:
            raise UserError(
                self.env._('Something went wrong during the token '
                           'generation. Please request a new authorization '
                           'code.')
            )

    def google_meet_company_refresh_token(self):
        """Helper method to refresh Google Meet token."""
        return self.action_google_meet_company_refresh_token()

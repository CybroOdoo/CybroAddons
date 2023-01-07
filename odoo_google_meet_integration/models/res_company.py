# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
##############################################################################

import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

TIMEOUT = 20


class ResCompany(models.Model):
    _inherit = "res.company"

    hangout_client_id = fields.Char(
        "Client Id", help='Google Developer Console Client ID')
    hangout_client_secret = fields.Char(
        "Client Secret", help='Google Developer Console Client Secret')
    hangout_redirect_uri = fields.Char(
        "Authorized redirect URIs", default="http://localhost:8016"
                                            "/google_meet_authentication", help='GoogleAuthorized redirect URIs')

    hangout_company_access_token = fields.Char('Access Token',
                                               copy=False)
    hangout_company_access_token_expiry = fields.Datetime(
        string='Token expiry')
    hangout_company_refresh_token = fields.Char('Refresh Token',
                                                copy=False)

    hangout_company_authorization_code = fields.Char("Authorization Code")

    def google_meet_company_authenticate(self):
        if not self.hangout_client_id:
            raise ValidationError("Please Enter Client ID")
        client_id = self.hangout_client_id
        if not self.hangout_redirect_uri:
            raise ValidationError("Please Enter Client Secret")
        redirect_url = self.hangout_redirect_uri
        calendar_scope = 'https://www.googleapis.com/auth/calendar'
        calendar_event_scope = 'https://www.googleapis.com/auth/calendar.events'
        url = (
            "https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
            "&access_type=offline&client_id={}&redirect_uri={}&scope={}+{} "
        ).format(client_id, redirect_url, calendar_scope,
                 calendar_event_scope)

        return {
            "type": 'ir.actions.act_url',
            "url": url,
            "target": "new"
        }

    def google_meet_company_refresh_token(self):
        if not self.hangout_client_id:
            raise UserError(
                _('Client ID is not yet configured.'))
        client_id = self.hangout_client_id

        if not self.hangout_client_secret:
            raise UserError(
                _('Client Secret is not yet configured.'))
        client_secret = self.hangout_client_secret

        if not self.hangout_company_refresh_token:
            raise UserError(
                _('Refresh Token is not yet configured.'))
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
        if response.json() and response.json().get('access_token'):
            self.write({
                'hangout_company_access_token':
                    response.json().get('access_token'),
            })
        else:
            raise UserError(
                _('Something went wrong during the token generation.'
                  ' Please request again an authorization code.')
            )

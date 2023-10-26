# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana jabin MP (odoo@cybrosys.com)
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
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError

TIMEOUT = 20


class ResCompany(models.Model):
    """Model for company with Google Meet integration settings."""
    _inherit = "res.company"

    client = fields.Char(string="Client ID",
                         help='Google Developer Console Client ID')
    client_secret = fields.Char(string="Client Secret",
                                help='Google Developer Console Client Secret')
    redirect_uri = fields.Char(string="Authorized redirect URIs",
                               default="http://localhost:8016/"
                                       "google_meet_authentication",
                               help='Google Authorized redirect URIs')
    company_access_token = fields.Char(string='Access Token', copy=False,
                                       help='The access token used for company'
                                            ' authentication.')
    company_access_token_expiry = fields.Datetime(string='Token expiry',
                                                  help='The expiry date and '
                                                       'time of  access token')
    company_refresh_token = fields.Char(string='Refresh Token', copy=False,
                                        help=' Refresh token used to obtain '
                                             'a new access token when the'
                                             ' current one expires.')
    company_authorization_code = fields.Char(string="Authorization Code",
                                             help='The authorization code'
                                                  'obtained during the company'
                                                  'authentication process.')

    def google_meet_company_authenticate(self):
        """Authenticate the company to access Google Meet APIs."""
        if not self.client or not self.client_secret or not self.redirect_uri:
            raise ValidationError(_(
                "Client ID, Client Secret, and Redirect URI are required."))
        calendar_scope = 'https://www.googleapis.com/auth/calendar'
        calendar_event_scope = ('https://www.googleapis.com/auth/calendar.'
                                'events')
        url = (
            "https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
            "&access_type=offline&client_id={}&redirect_uri={}&scope={}+{} "
        ).format(self.client, self.redirect_uri, calendar_scope,
                 calendar_event_scope)
        return {
            "type": 'ir.actions.act_url',
            "url": url,
            "target": "new"
        }

    def google_meet_company_refresh_token(self):
        """Refresh the access token for the company."""
        if not all(
                [self.client, self.client_secret, self.company_refresh_token]):
            raise UserError(
                _('Client ID, Client Secret, and Refresh Token are required.'))
        data = {
            'client_id': self.client,
            'client_secret': self.client_secret,
            'refresh_token': self.company_refresh_token,
            'grant_type': 'refresh_token',
        }
        response = requests.post(
            'https://accounts.google.com/o/oauth2/token', data=data,
            headers={
                'content-type': 'application/x-www-form-urlencoded'},
            timeout=TIMEOUT)
        if response.ok and response.json().get('access_token'):
            self.write({
                'company_access_token': response.json().get('access_token'),
            })
        else:
            raise UserError(
                _('Something went wrong during the token generation. '
                  'Please request a new authorization code.'))

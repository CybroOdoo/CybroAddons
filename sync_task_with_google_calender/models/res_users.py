# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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
#############################################################################
import requests
import re
from datetime import timedelta
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.addons.google_account.models.google_service import \
    GOOGLE_TOKEN_ENDPOINT


class ResUsers(models.Model):
    """Extend res.users model to include Google Calendar integration."""

    _inherit = 'res.users'

    refresh_token = fields.Char(string='Refresh Token',
                                help='Refresh token used for token '
                                     'authentication with Google Calendar'
                                     ' service.')
    user_token = fields.Char(string='User Token',
                             help='User token or access token obtained from '
                                  'Google Calendar service.')
    last_sync_date = fields.Datetime(string='Token Validity',
                                     help='Date and time indicating the '
                                          'validity'
                                          ' period of the user token.')
    api_key = fields.Char(string="Enter API Key",
                          help='API key required for authentication and access '
                               'to Google Calendar service.')
    google_user_mail = fields.Char(string='User Mail',
                                   help='The Mail address where the task is '
                                        'to be created')

    def _set_auth_tokens(self, access_token, refresh_token, ttl):
        """Set the authentication tokens for the user."""
        self.write({
            'refresh_token': refresh_token,
            'user_token': access_token,
            'last_sync_date': fields.Datetime.now() + timedelta(
                seconds=ttl) if ttl else False,
        })

    def authenticate_button(self):
        """Authenticate the user with Google Calendar service."""
        self.ensure_one()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        client_id = get_param('google_calendar_client_id')
        client_secret = get_param('google_calendar_client_secret')
        if not client_id or not client_secret:
            raise UserError(_("The account for the Google Calendar "
                              "service is not configured."))
        # Validate the API key and email credentials
        if not (self.api_key and len(
                self.api_key) > 10 and self.is_valid_email()):
            raise UserError(_("Invalid credentials. Please provide valid "
                              "API key or  email."))
        self.refresh_token = self.google_calendar_account_id.calendar_rtoken
        self.user_token = self.google_calendar_account_id.calendar_token
        self.last_sync_date = self.google_calendar_account_id. \
            calendar_token_validity
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Successful'),
                'type': 'success',
                'message': 'Authentication successful!',
                'sticky': True,
            }
        }
        return notification

    def is_valid_email(self):
        """ Return True if the email is valid, False otherwise"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if self.google_user_mail and re.match(pattern, self.google_user_mail):
            return True
        return False

    def refresh_button(self):
        """Refresh the user token using the refresh token."""
        get_param = self.env['ir.config_parameter'].sudo().get_param
        client_id = get_param('google_calendar_client_id')
        client_secret = get_param('google_calendar_client_secret')
        if not client_id or not client_secret:
            raise UserError(
                _("The account for the Google Calendar service is"
                  " not configured."))
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            'refresh_token': self.refresh_token,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
        }
        try:
            _dummy, response, _dummy = self.env['google.service']._do_request(
                GOOGLE_TOKEN_ENDPOINT, params=data,
                headers=headers, method='POST', preuri='')
            ttl = response.get('expires_in')
            self.write({
                'user_token': response.get('access_token'),
                'last_sync_date': fields.Datetime.now() + timedelta(
                    seconds=ttl),
            })
        except requests.HTTPError as error:
            if error.response.status_code in (
                    400, 401):  # invalid grant or invalid client
                # Delete refresh token and make sure it's committed
                self.env.cr.rollback()
                self._set_auth_tokens(False, False, 0)
                self.env.cr.commit()
            error_key = error.response.json().get("error", "nc")
            error_msg = _(
                "An error occurred while generating the token. "
                "Your authorization code may be invalid or has already"
                " expired [%s].You should check your Client ID and secret on "
                "the Google APIs platform  try to stop and restart your "
                "calendar synchronization.",
                error_key)
            raise UserError(error_msg)

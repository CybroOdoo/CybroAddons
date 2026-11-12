# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK (odoo@cybrosys.com)
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
from datetime import timedelta
from urllib.parse import urlencode, urlparse

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import consteq
from odoo.tools.misc import hmac

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
OAUTH_STATE_SCOPE = "google_drive_odoo_connector.oauth_state"


class GoogleDriveAccount(models.Model):
    """Model representing Google Drive account configuration and OAuth
    connection."""
    _name = 'google.drive.account'
    _description = 'Google Drive Account'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    state = fields.Selection([
        ('draft', 'Not Connected'),
        ('connected', 'Connected'),
        ('error', 'Error')],
        string='State', default='draft')
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    refresh_token = fields.Text(string='Refresh Token')
    access_token = fields.Text(string='Access Token')
    token_expiry = fields.Datetime(string='Token Expiration')
    drive_folder_id = fields.Char(
        string='Drive Folder ID',
        help="ID of the Google Drive folder where attachments are uploaded."
             " Leave empty to upload to the root of My Drive.")
    keep_local_copy = fields.Boolean(
        string="Keep Local Copy",
        help="If disabled, the attachment binary will be removed from Odoo"
             " after a successful upload to Google Drive."
    )

    @api.model
    def _get_connected_account(self):
        """Return the connected Google Drive account (as superuser).

        The account holds OAuth secrets, so it is only accessible to
        administrators; attachment sync must work for every user.

        :return: Connected google.drive.account record or an empty recordset.
        :rtype: google.drive.account
        """
        return self.sudo().search([("state", "=", "connected")], limit=1)

    def _get_redirect_uri(self):
        """Return the OAuth redirect URI registered in the Google Console.

        Google only accepts plain http redirect URIs for localhost, so a
        non-local http base URL is rewritten to localhost.

        :return: Redirect URI of the OAuth callback route.
        :rtype: str
        """
        ICP = self.env["ir.config_parameter"].sudo()
        redirect_uri = ICP.get_param("google_drive.redirect_uri")
        if redirect_uri:
            return redirect_uri
        redirect_uri = (ICP.get_param("web.base.url")
                        + "/google_drive/oauth/callback")
        parsed = urlparse(redirect_uri)
        if (parsed.scheme == "http"
                and parsed.hostname not in ("localhost", "127.0.0.1")):
            port_str = f":{parsed.port}" if parsed.port else ""
            redirect_uri = f"http://localhost{port_str}{parsed.path}"
        return redirect_uri

    def _get_oauth_state(self):
        """Return the signed OAuth state identifying this account.

        :return: State value in the form ``<id>:<signature>``.
        :rtype: str
        """
        self.ensure_one()
        return "%s:%s" % (
            self.id, hmac(self.env(su=True), OAUTH_STATE_SCOPE, self.id))

    @api.model
    def _get_account_from_oauth_state(self, state):
        """Return the account matching a signed OAuth state.

        :param str state: State value returned by Google.
        :return: Matching google.drive.account or an empty recordset if the
            state is malformed or its signature is invalid.
        :rtype: google.drive.account
        """
        account_id, dummy, signature = (state or "").partition(":")
        if not account_id.isdigit():
            return self.browse()
        expected = hmac(self.env(su=True), OAUTH_STATE_SCOPE, int(account_id))
        if not consteq(signature, expected):
            return self.browse()
        return self.browse(int(account_id)).exists()

    def _get_headers(self):
        """Construct authorization headers with a valid OAuth access token.

        Refreshes the access token automatically if it is missing or has
        expired.

        :return: Dictionary containing the Authorization HTTP header.
        :rtype: dict
        """
        self.ensure_one()
        if (not self.access_token or not self.token_expiry
                or self.token_expiry <= fields.Datetime.now()):
            self._refresh_access_token()
        return {
            "Authorization": f"Bearer {self.access_token}"
        }

    def action_connect(self):
        """Initiate OAuth 2.0 authorization flow with Google.

        Redirects the user to Google's authorization consent screen.

        :return: Action dictionary directing user to Google OAuth URL.
        :rtype: dict
        """
        self.ensure_one()
        params = {
            "client_id": self.client_id,
            "redirect_uri": self._get_redirect_uri(),
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/drive",
            "access_type": "offline",
            "prompt": "consent",
            "state": self._get_oauth_state(),
        }
        url = ("https://accounts.google.com/o/oauth2/v2/auth?"
               + urlencode(params))
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }

    def exchange_authorization_code(self, code):
        """Exchange the OAuth authorization code for access and refresh tokens.

        :param str code: Authorization code returned by Google OAuth redirect.
        :raises UserError: If token exchange fails.
        """
        self.ensure_one()
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self._get_redirect_uri(),
        }
        response = requests.post(GOOGLE_TOKEN_URL, data=payload, timeout=30)
        if response.status_code != 200:
            raise UserError(_(
                "Google authorization failed: %s", response.text))
        token = response.json()
        expiry = (
            fields.Datetime.now()
            + timedelta(seconds=token["expires_in"])
        )
        self.write({
            "access_token": token["access_token"],
            "refresh_token": token.get("refresh_token"),
            "token_expiry": expiry,
            "state": "connected",
        })

    def _refresh_access_token(self):
        """Request a new OAuth access token using the stored refresh token.

        :raises UserError: If refresh token is missing or token renewal fails.
        """
        self.ensure_one()
        if not self.refresh_token:
            raise UserError(_("No refresh token available."))
        response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        token_data = response.json()
        if response.status_code != 200:
            if token_data.get("error") == "invalid_grant":
                self.write({
                    "state": "error",
                    "access_token": False,
                })
                raise UserError(_(
                    "Google authorization has expired.\n"
                    "Please reconnect your account."
                ))
            raise UserError(_(
                "Could not refresh the Google access token: %s",
                response.text))
        expires_in = token_data.get("expires_in", 3600)
        self.write({
            "access_token": token_data["access_token"],
            "token_expiry": fields.Datetime.now() + timedelta(
                seconds=expires_in - 60),
        })

    def action_test_connection(self):
        """Test API connectivity by fetching a list of files from Google Drive.

        :return: Client notification action indicating successful connection.
        :rtype: dict
        :raises UserError: If Google Drive API returns an error response.
        """
        self.ensure_one()
        response = requests.get(
            "https://www.googleapis.com/drive/v3/files?pageSize=10",
            headers=self._get_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            raise UserError(_(
                "Google Drive connection failed: %s", response.text))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Connection successful'),
                'type': 'success',
            }
        }

    def download_file(self, file_id):
        """Download raw binary content of a file from Google Drive.

        :param str file_id: Unique ID of the file in Google Drive.
        :return: Raw binary content of the file.
        :rtype: bytes
        """
        self.ensure_one()
        response = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
            headers=self._get_headers(),
            timeout=60,
        )
        response.raise_for_status()
        return response.content

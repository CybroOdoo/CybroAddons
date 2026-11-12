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
import logging

from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class GoogleDriveController(http.Controller):
    """HTTP controller for handling Google Drive OAuth callbacks."""

    @http.route('/google_drive/oauth/callback', type='http', auth='user')
    def oauth_callback(self, code=None, state=None, error=None, **kwargs):
        """Handle the OAuth 2.0 authorization callback from Google.

        Exchanges the authorization code for tokens and redirects to the
        account form.

        :param str code: OAuth authorization code returned by Google.
        :param str state: Signed state identifying the google.drive.account.
        :param str error: Error message if authorization failed on Google side.
        :return: HTTP response or redirect response to account form view.
        :rtype: odoo.http.Response
        """
        if error:
            return request.make_response(error)
        if not code:
            return request.make_response(_("Authorization code missing."))
        if not state:
            return request.make_response(_("State missing."))
        account = request.env[
            "google.drive.account"]._get_account_from_oauth_state(state)
        if not account:
            return request.make_response(_("Invalid state."), status=400)
        try:
            account.exchange_authorization_code(code)
        except UserError as exc:
            _logger.warning(
                "Google Drive authorization failed for account %s: %s",
                account.id, exc)
            account.state = 'error'
        return request.redirect(
            "/odoo/action-google_drive_odoo_connector."
            "action_google_drive_config/%s" % account.id)

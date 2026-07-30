# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import _, http
from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.web.controllers.utils import ensure_db


class AuthLoginHome(Home):
    """Inherit AuthSignupHome to handle GitHub OAuth login errors and provider listing."""

    @http.route()
    def web_login(self, *args, **kw):
        """Override web_login to display GitHub OAuth providers and handle OAuth error codes.

        Handles GET redirect for already-authenticated users, lists available
        OAuth providers, and maps OAuth error codes to user-friendly messages
        in the login page context.
        """
        ensure_db()

        if request.httprequest.method == 'GET' and request.session.uid:
            redirect_url = request.params.get('redirect')
            if redirect_url:
                return request.redirect(redirect_url)

        providers = self.list_providers()
        response = super(OAuthLogin, self).web_login(*args, **kw)

        if response.is_qweb:
            error_messages = {
                '1': _("You are not allowed to signup on this database."),
                '2': _("Access Denied"),
                '3': _(
                    "Email Already Exists.\nPlease contact your "
                    "Administrator."),
                '4': _(
                    "Validation Endpoint either Not present or invalid.\n"
                    "Please contact your Administrator."),
                '5': _(
                    "Github OAuth API Failed, For more information please "
                    "contact Administrator."),
                '6': _(
                    "Github OAuth API Failed,\nClient ID or Client Secret Not"
                    " present or has been compromised.\n"
                    "For more information please contact Administrator."),
            }
            error_code = request.params.get('oauth_error')
            error_message = error_messages.get(error_code)
            response.qcontext.update({
                'providers': providers,
                'error': error_message,
            })
        return response

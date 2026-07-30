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
import json
import logging

import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class GithubOAuthCallbackHandler(http.Controller):
    """Handle the GitHub OAuth callback to exchange authorization code for an access token."""

    @http.route(['/oauth/callback'], auth='public', csrf=False,
                methods=['GET', 'POST'], type='http')
    def get_oauth_token(self, **post):
        """Process the OAuth callback and redirect to the sign-in route with the access token.

        Extracts the OAuth provider from the state parameter, retrieves the
        client credentials, and exchanges the authorization code for an access
        token. Redirects the user to the auth_oauth/signin route with the
        token appended as a query parameter.
        """
        state = post.get('state')
        if state:
            try:
                provider_id = json.loads(state).get('p')
                provider = (request.env['auth.oauth.provider'].sudo()
                            .browse(provider_id))
            except (json.JSONDecodeError, ValueError):
                _logger.error('Invalid state parameter: %s', state)
                return werkzeug.utils.redirect(
                    "/web/login?oauth_error=4", 303)
        else:
            provider = request.env.ref(
                'github_login_odoo.auth_oauth_provider_github').sudo()

        base_redirect_url = (request.httprequest.url_root
                             + "auth_oauth/signin")

        if post.get("code"):
            client_id = provider.client_id
            client_secret = provider.client_secret

            if not client_id or not client_secret:
                _logger.info(
                    'OAuth2: Missing Client ID or Client Secret. '
                    'Redirecting to login page.')
                return werkzeug.utils.redirect(
                    "/web/login?oauth_error=6", 303)

            query_params = {
                'access_token': post.get("code"),
                'state': state,
                'provider': provider.id,
            }
            redirect_url = "{}?{}".format(
                base_redirect_url,
                werkzeug.urls.url_encode(query_params))
            return werkzeug.utils.redirect(redirect_url)

        _logger.warning(
            "OAuth2: Code not present in post data. "
            "Redirecting to login page.")
        return werkzeug.utils.redirect("/web/login?oauth_error=4", 303)
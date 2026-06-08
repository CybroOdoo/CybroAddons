# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################

import json
import logging
import werkzeug
from odoo import _, http, SUPERUSER_ID
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import (fragment_to_query_string,
                                                    OAuthController, OAuthLogin)
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.web.controllers.utils import _get_login_redirect_url, ensure_db
from werkzeug.exceptions import BadRequest


_logger = logging.getLogger(__name__)


class OAuthLogin(OAuthLogin):
    """Controller to login"""

    @http.route()
    def web_login(self, *args, **kw):
        """
            Override the web login method to handle OAuth errors and display
            available OAuth providers.
        """
        ensure_db()

        # Handle redirection if already logged in
        if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
            return request.redirect(request.params.get('redirect'))

        # List OAuth providers
        providers = self.list_providers()

        # Call parent class login method
        response = super().web_login(*args, **kw)

        # Process response if it is a QWeb template
        if response.is_qweb:
            # Define error messages
            error_messages = {
                '1': _("You are not allowed to signup on this database."),
                '2': _("Access Denied"),
                '3': _("Email Already Exists.\nPlease contact your Administrator."),
                '4': _("Validation Endpoint either Not present or invalid.\nPlease contact your Administrator."),
                '5': _("Github OAuth API Failed, For more information please contact Administrator."),
                '6': _("Github OAuth API Failed,\nClient ID or Client Secret Not present or has been compromised.\nFor more information please contact Administrator.")
            }

            # Get the error message
            error_code = request.params.get('oauth_error')
            if error_code:
                error_message = error_messages.get(error_code)
                if error_message:
                    response.qcontext['error'] = error_message

            response.qcontext['providers'] = providers
        return response


    def list_providers(self):
        """
            Retrieve a list of enabled OAuth providers and update auth_link for GitHub.
        """
        providers = super().list_providers()
        for provider in providers:
            if provider.get('name') and 'github' in provider.get('name').lower():
                state = self.get_state(provider)
                params = dict(
                    client_id=provider['client_id'],
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
                provider['auth_link'] = ("%s?%s"
                                            % (provider['auth_endpoint'],
                                            werkzeug.urls.url_encode(params)))
        return providers


class GitHubOAuthController(OAuthController):
    """Controller to sign in to home page"""

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kw):
        """
            Handle OAuth sign-in redirection and user authentication.
        """
        # Extract and validate state parameters
        state_json = kw.get('state', '{}')
        try:
            state = json.loads(state_json)
        except json.JSONDecodeError:
            _logger.error("Invalid state parameter: %s", state_json)
            return BadRequest()

        dbname = state.get('d')
        if not dbname or not http.db_filter([dbname]):
            return BadRequest()

        # Ensure database and use request environment
        ensure_db(db=dbname)

        provider = state.get('p')
        context = state.get('c', {})
        action = state.get('a')
        menu = state.get('m')
        redirect_url = state.get('r')

        try:
            _logger.info("GitHub OAuth signin: Starting for db %s, provider %s", dbname, provider)
            context.update({'provider': provider, 'github': True})
            # Use request.env with SUPERUSER_ID and updated context
            request.update_context(**context)
            _logger.info("GitHub OAuth signin: Calling auth_oauth with kw keys: %s", list(kw.keys()))
            _, login, key = request.env['res.users'].with_user(SUPERUSER_ID).auth_oauth(provider, kw)
            _logger.info("GitHub OAuth signin: auth_oauth returned login %s", login)
            request.env.cr.commit()

            # Determine the redirection URL
            if redirect_url:
                url = werkzeug.urls.url_unquote_plus(redirect_url)
            else:
                url = '/web'
                if action:
                    url = f'/web#action={action}'
                elif menu:
                    url = f'/web#menu_id={menu}'

            # Authenticate session and handle redirection
            _logger.info("GitHub OAuth signin: Authenticating session for login %s", login)
            credential = {'login': login, 'token': key, 'type': 'oauth_token'}
            auth_info = request.session.authenticate(request.env, credential)
            _logger.info("GitHub OAuth signin: Session authenticated for uid %s", auth_info['uid'])
            resp = request.redirect(_get_login_redirect_url(auth_info['uid'], url), 303)
            resp.autocorrect_location_header = False
            # Adjust location header if necessary
            if werkzeug.urls.url_parse(resp.location).path == '/web':
                resp.location = '/'
            return resp
        except AttributeError:
            _logger.error(
                "auth_signup not installed on database %s: oauth sign up "
                "cancelled.",
                dbname)
            return request.redirect("/web/login?oauth_error=1", 303)

        except AccessDenied:
            _logger.info(
                'OAuth2: access denied, redirecting to main page if a valid '
                'session exists.')
            return request.redirect("/web/login?oauth_error=3", 303)

        except Exception as e:
            _logger.exception("OAuth2 error: %s", str(e))
            return request.redirect("/web/login?oauth_error=2", 303)


class CallbackHandler(http.Controller):
    """Controller for call back URL"""

    @http.route(['/oauth/callback'], auth='public', csrf=False,
                methods=['GET', 'POST'], type='http')
    def get_oauth_token(self, **post):
        """
            Handle OAuth callback to retrieve access token.
        """
        # Determine OAuth provider
        state = post.get('state')
        if state:
            try:
                provider_id = json.loads(state).get('p')
                provider = request.env['auth.oauth.provider'].sudo().browse(
                    provider_id)
            except (json.JSONDecodeError, ValueError):
                _logger.error('Invalid state parameter: %s', state)
                return werkzeug.utils.redirect("/web/login?oauth_error=4", 303)
        else:
            provider = request.env.ref(
                'github_login_odoo.auth_oauth_provider_github').sudo()

        # Prepare redirect URL
        base_redirect_url = request.httprequest.url_root + "auth_oauth/signin"

        # Handle OAuth code and redirection
        if post.get("code"):
            client_id = provider.client_id
            client_secret = provider.client_secret

            if not client_id or not client_secret:
                _logger.info(
                    'OAuth2: Missing Client ID or Client Secret. Redirecting to '
                    'login page.')
                return werkzeug.utils.redirect("/web/login?oauth_error=6", 303)

            # Build redirect URL with query parameters
            query_params = {
                'access_token': post.get("code"),
                'state': state,
                'provider': provider.id
            }
            redirect_url = (f"{base_redirect_url}?"
                            f"{werkzeug.urls.url_encode(query_params)}")

            return werkzeug.utils.redirect(redirect_url)

        # Handle missing code in post data
        _logger.warning(
            "OAuth2: Code not present in post data. Redirecting to login page.")
        return werkzeug.utils.redirect("/web/login?oauth_error=4", 303)

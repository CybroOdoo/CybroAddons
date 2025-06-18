# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import _, api, http, SUPERUSER_ID
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import (fragment_to_query_string,
                                                    OAuthController, OAuthLogin)
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.web.controllers.utils import _get_login_redirect_url, ensure_db
from werkzeug.exceptions import BadRequest
from odoo import registry as registry_get


_logger = logging.getLogger(__name__)


class AuthLoginHome(Home):
    """HTTP controller to login via github"""

    @http.route()
    def web_login(self, *args, **kw):
        """
            Override the web login method to handle OAuth errors and display
            available OAuth providers.

        """
        ensure_db()

        # Handle redirection if the request method is GET, user is
        # authenticated, and redirect URL is provided
        if request.httprequest.method == 'GET' and request.session.uid:
            redirect_url = request.params.get('redirect')
            if redirect_url:
                return request.redirect(redirect_url)

        # List OAuth providers
        providers = self.list_providers()

        # Call parent class login method
        response = super(OAuthLogin, self).web_login(*args, **kw)

        # Process response if it is a QWeb template
        if response.is_qweb:
            # Define error messages in a dictionary
            error_messages = {
                '1': _("You are not allowed to signup on this database."),
                '2': _("Access Denied"),
                '3': _(
                    "Email Already Exists.\nPlease contact your "
                    "Administrator."),
                '4': _(
                    "Validation Endpoint either Not present or invalid.\nPlease"
                    "contact your Administrator."),
                '5': _(
                    "Github OAuth API Failed, For more information please "
                    "contact Administrator."),
                '6': _(
                    "Github OAuth API Failed,\nClient ID or Client Secret Not"
                    " present or has been compromised.\n"
                    "For more information please contact Administrator.")
            }

            # Get the error message if an OAuth error code is present
            error_code = request.params.get('oauth_error')
            error_message = error_messages.get(error_code)

            # Add providers and error message to the response context
            response.qcontext.update({
                'providers': providers,
                'error': error_message
            })
        return response


class GitHubOAuthController(OAuthController):
    """Controller to sign in to home page"""

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kw):
        """
            Handle OAuth sign-in redirection and user authentication.

            This route is responsible for processing the OAuth sign-in callback
            and initiating the user authentication
            process.
            It retrieves the database name, OAuth provider, and other context
            information from the state parameter.
            The user authentication is performed using the OAuth credentials
            provided in the request.
            After successful authentication, the user is redirected to the
            appropriate page based on the state
            parameters.

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

        provider = state.get('p')
        context = state.get('c', {})
        action = state.get('a')
        menu = state.get('m')
        redirect_url = state.get('r')

        # Get registry and authenticate
        registry = registry_get(dbname)
        try:
            with registry.cursor() as cr:
                context.update({'provider': provider, 'github': True})
                env = api.Environment(cr, SUPERUSER_ID, context)
                db, login, key = env['res.users'].sudo().auth_oauth(provider,
                                                                    kw)
                cr.commit()
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
                pre_uid = request.session.authenticate(db, login, key)
                resp_url = _get_login_redirect_url(pre_uid, url)
                resp = request.redirect(resp_url, 303)
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


class OAuthLogin(OAuthLogin):
    """Controller to login"""
    def list_providers(self):
        """
            Retrieve a list of enabled OAuth providers.

            This method queries the database for OAuth providers that are
            enabled.
            For each provider, it generates an authentication link based on
            the provider's details.
            The authentication link is used to initiate the OAuth authentication
             process.

        """
        try:
            providers = (request.env['auth.oauth.provider'].sudo().
                            search_read([('enabled', '=', True)]))
        except Exception:
            providers = []
        for provider in providers:
            state = self.get_state(provider)
            if provider.get('name') in ['GitHub', 'github']:
                params = dict(
                    client_id=provider['client_id'],
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
                provider['auth_link'] = ("%s?%s"
                                            % (provider['auth_endpoint'],
                                            werkzeug.urls.url_encode(params)))
            else:
                return_url = request.httprequest.url_root + 'auth_oauth/signin'
                params = dict(
                    response_type='token',
                    client_id=provider['client_id'],
                    redirect_uri=return_url,
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
                provider['auth_link'] = ("%s?%s"
                                            % (provider['auth_endpoint'],
                                            werkzeug.urls.url_encode(params)))
        return providers


class CallbackHandler(http.Controller):
    """Controller for call back URL"""

    @http.route(['/oauth/callback'], auth='public', csrf=False,
                methods=['GET', 'POST'], type='http')
    def get_oauth_token(self, **post):
        """
            Handle OAuth callback to retrieve access token.

            This route handles the OAuth callback after a user has authenticated
             with an OAuth provider.
            It extracts the state and provider information from the request
            parameters to identify the OAuth provider.
            Based on the provider, it retrieves the client ID and client secret
            to exchange the authorization code for
            an access token.
            The access token is then appended to the redirect URL and the user
            is redirected to the sign-in page with
            the token.
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
                'github_oauth_app.auth_oauth_provider_github').sudo()

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

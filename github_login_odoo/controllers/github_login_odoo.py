# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import json
import logging
from urllib.parse import urlencode

from werkzeug.exceptions import BadRequest

from odoo import _, http
from odoo.http import request
from odoo.http.router import db_filter
from odoo.addons.auth_oauth.controllers.main import (fragment_to_query_string,
                                                    OAuthController, OAuthLogin)
from odoo.addons.web.controllers.utils import ensure_db


_logger = logging.getLogger(__name__)


class GitHubOAuthLogin(OAuthLogin):
    """Controller to log in with GitHub OAuth support."""

    @http.route(type='http')
    def web_login(self, *args, **kw):
        """
        Override the web login method to handle custom OAuth errors and display
        available OAuth providers.
        """
        ensure_db()
        # Handle redirection if already logged in
        if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
            return request.redirect(request.params.get('redirect'))
        # List OAuth providers
        providers = self.list_providers()
        # Call parent class login method (handles standard oauth_error 1, 2, 3)
        response = super().web_login(*args, **kw)
        # Process response if it is a QWeb template
        if response.is_qweb:
            # Custom error messages for GitHub OAuth (standard 1, 2, 3 are handled by super)
            github_error_messages = {
                '4': _("Validation endpoint is missing or invalid.\nPlease contact your administrator."),
                '5': _("GitHub OAuth API failed. For more information, please contact your administrator."),
                '6': _("GitHub OAuth API failed.\nClient ID or Client Secret is not present or has been compromised.\nFor more information, please contact your administrator."),
            }
            error_code = request.params.get('oauth_error')
            if error_code in github_error_messages:
                response.qcontext['error'] = github_error_messages[error_code]

            response.qcontext['providers'] = providers
        return response

    def list_providers(self):
        """
        Retrieve a list of enabled OAuth providers and update auth_link for GitHub
        based on provider is_github flag or auth_endpoint.
        """
        providers = super().list_providers()
        for provider in providers:
            is_github = provider.get('is_github') or (
                provider.get('auth_endpoint') and 'github' in provider.get('auth_endpoint').lower()
            )
            if is_github:
                state = self.get_state(provider)
                params = dict(
                    client_id=provider['client_id'],
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
                provider['auth_link'] = "%s?%s" % (
                    provider['auth_endpoint'],
                    urlencode(params),
                )
        return providers


class GitHubOAuthController(OAuthController):
    """Controller to sign in with OAuth support."""

    @http.route('/auth_oauth/signin', type='http', auth='none', readonly=False)
    @fragment_to_query_string
    def signin(self, **kw):
        """
        Handle OAuth sign-in redirection and user authentication.
        Ensures GitHub context is only set when the OAuth provider is GitHub.
        For Google and other OAuth providers, standard flow is preserved.
        """
        state_json = kw.get('state', '{}')
        try:
            state = json.loads(state_json)
        except (json.JSONDecodeError, TypeError):
            _logger.error("Invalid state parameter: %s", state_json)
            raise BadRequest()

        dbname = state.get('d')
        if not dbname or not db_filter([dbname]):
            raise BadRequest()
        ensure_db(db=dbname)

        provider_id = state.get('p')
        if provider_id:
            try:
                provider = request.env['auth.oauth.provider'].sudo().browse(provider_id)
                if provider.exists() and provider.is_github:
                    context = state.setdefault('c', {})
                    context.update({'provider': provider_id, 'github': True})
                    kw['state'] = json.dumps(state)
            except Exception as e:
                _logger.warning("Error checking OAuth provider in signin: %s", e)

        return super().signin(**kw)


class CallbackHandler(http.Controller):
    """Controller for callback URL"""

    @http.route(['/oauth/callback'], auth='public', csrf=False,
                methods=['GET', 'POST'], type='http')
    def get_oauth_token(self, **post):
        """
        Handle OAuth callback to retrieve access token.
        """
        # Handle user cancellation or provider error
        if post.get("error") == "access_denied":
            _logger.info("OAuth2: User denied access.")
            return request.redirect("/web/login?oauth_error=2", 303)
        if post.get("error"):
            _logger.error("OAuth2 error in callback: %s (%s)", post.get("error"), post.get("error_description"))
            return request.redirect("/web/login?oauth_error=5", 303)

        # Determine OAuth provider
        state = post.get('state')
        if state:
            try:
                provider_id = json.loads(state).get('p')
                provider = request.env['auth.oauth.provider'].sudo().browse(provider_id)
                if not provider.exists():
                    _logger.error('Provider with id %s not found', provider_id)
                    return request.redirect("/web/login?oauth_error=4", 303)
            except (json.JSONDecodeError, ValueError, TypeError):
                _logger.error('Invalid state parameter: %s', state)
                return request.redirect("/web/login?oauth_error=4", 303)
        else:
            provider = request.env.ref(
                'github_login_odoo.auth_oauth_provider_github', raise_if_not_found=False)
            if provider:
                provider = provider.sudo()
            else:
                return request.redirect("/web/login?oauth_error=4", 303)

        # Prepare redirect URL
        base_redirect_url = request.httprequest.url_root + "auth_oauth/signin"
        # Handle OAuth code and redirection
        if post.get("code"):
            client_id = provider.client_id
            client_secret = provider.client_secret
            if not client_id or not client_secret:
                _logger.info(
                    'OAuth2: Missing Client ID or Client Secret. Redirecting to login page.')
                return request.redirect("/web/login?oauth_error=6", 303)
            # Build redirect URL with query parameters
            query_params = {
                'access_token': post.get("code"),
                'state': state,
                'provider': provider.id,
            }
            redirect_url = f"{base_redirect_url}?{urlencode(query_params)}"
            return request.redirect(redirect_url)

        # Handle missing code in post data
        _logger.warning("OAuth2: Code not present in post data. Redirecting to login page.")
        return request.redirect("/web/login?oauth_error=4", 303)

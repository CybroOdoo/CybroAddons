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
from werkzeug.exceptions import BadRequest

from odoo import api, http, SUPERUSER_ID
from odoo import registry as registry_get
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import (
    fragment_to_query_string, OAuthController)
from odoo.addons.web.controllers.utils import _get_login_redirect_url

_logger = logging.getLogger(__name__)


class GitHubOAuthController(OAuthController):
    """Inherit OAuthController from auth_oauth to handle GitHub OAuth sign-in callback."""

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kw):
        """Process the GitHub OAuth sign-in callback and authenticate the user session.

        Parses the state parameter to extract database, provider, and redirect
        information. Authenticates the user via GitHub OAuth credentials and
        redirects to the appropriate page based on user group membership.
        """
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

        registry = registry_get(dbname)
        try:
            with registry.cursor() as cr:
                context.update({'provider': provider, 'github': True})
                env = api.Environment(cr, SUPERUSER_ID, context)
                db, login, key = env['res.users'].sudo().auth_oauth(
                    provider, kw)
                cr.commit()

                credential = {
                    'login': login,
                    'token': key,
                    'type': 'oauth_token',
                }
                pre_uid = request.session.authenticate(db, credential)
                actual_uid = (pre_uid.get('uid')
                              if isinstance(pre_uid, dict) else pre_uid)

                user = env['res.users'].browse(actual_uid)
                is_internal = user.has_group('base.group_user')

                if not is_internal:
                    url = '/my'
                else:
                    if redirect_url:
                        url = werkzeug.urls.url_unquote_plus(redirect_url)
                    else:
                        url = '/web'
                        if action:
                            url = '/web#action={}'.format(action)
                        elif menu:
                            url = '/web#menu_id={}'.format(menu)

                resp_url = _get_login_redirect_url(actual_uid, url)
                resp = request.redirect(resp_url, 303)
                if werkzeug.urls.url_parse(resp.location).path == '/web':
                    resp.location = '/'
                return resp

        except AttributeError:
            _logger.error(
                "auth_signup not installed on database %s: oauth sign up "
                "cancelled.", dbname)
            return request.redirect("/web/login?oauth_error=1", 303)

        except AccessDenied:
            _logger.info(
                'OAuth2: access denied, redirecting to main page if a valid '
                'session exists.')
            return request.redirect("/web/login?oauth_error=3", 303)

        except Exception as e:
            _logger.exception("OAuth2 error: %s", str(e))
            return request.redirect("/web/login?oauth_error=2", 303)

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

import werkzeug

from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as BaseOAuthLogin


class OAuthLogin(BaseOAuthLogin):
    """Inherit OAuthLogin from auth_oauth to customize GitHub authentication link generation."""

    def list_providers(self):
        """Retrieve enabled OAuth providers and build their authentication links.

        For GitHub providers, builds an auth link using client_id, scope, and
        state. For all other providers, builds a standard OAuth2 token redirect
        link including the redirect_uri.
        """
        try:
            providers = (request.env['auth.oauth.provider'].sudo()
                         .search_read([('enabled', '=', True)]))
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
            else:
                return_url = (request.httprequest.url_root
                              + 'auth_oauth/signin')
                params = dict(
                    response_type='token',
                    client_id=provider['client_id'],
                    redirect_uri=return_url,
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
            provider['auth_link'] = "{}?{}".format(
                provider['auth_endpoint'],
                werkzeug.urls.url_encode(params))
        return providers

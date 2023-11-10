"""Microsoft azure login"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
import json
import werkzeug.urls
import werkzeug.utils
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home


class OAuthLogin(Home):
    """This class is used for oauth login"""

    def list_providers(self):
        """Which provides the oauth provider to login to the odoo"""
        super().list_providers()
        try:
            auth_providers = request.env[
                'auth.oauth.provider'].sudo().search_read(
                [('enabled', '=', True)])
        except Exception:
            auth_providers = []
        for rec in auth_providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = self.get_state(rec)
            params = dict(
                response_type=rec['response_type'],
                client_id=rec['client_id'],
                redirect_uri=return_url,
                scope=rec['scope'],
                state=json.dumps(state),
            )
            rec['auth_link'] = "%s?%s" % (
                rec['auth_endpoint'], werkzeug.urls.url_encode(params))
        return auth_providers

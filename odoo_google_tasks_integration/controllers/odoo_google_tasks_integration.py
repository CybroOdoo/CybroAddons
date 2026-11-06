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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from markupsafe import escape

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools import consteq


class GoogleTaskAuth(http.Controller):
    """Receive the authorization code from Google"""

    @http.route('/google_task_authentication', type='http', auth='user')
    def get_auth_code(self, code=None, state=None, error=None, **_kwargs):
        """Exchange the authorization code for tokens"""
        if not request.env.user.has_group('project.group_project_manager'):
            raise request.not_found()
        credential = request.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data')
        if not state or not consteq(state, credential._get_oauth_state()):
            return request.env._('Invalid authentication request. Click '
                                 'Authenticate again in Odoo.')
        if error or not code:
            return escape(request.env._(
                'Google did not authorize the access: %s',
                error or request.env._('no authorization code')))
        try:
            credential._exchange_authorization_code(code)
        except UserError as exc:
            return escape(str(exc))
        return request.env._('Authentication Success. You can close this '
                             'window.')

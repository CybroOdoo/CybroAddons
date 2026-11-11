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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import json
import logging
from urllib.parse import urlparse

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class OnedriveAuth(http.Controller):
    """Handle OAuth2 callback from Microsoft OneDrive."""

    @http.route('/onedrive/authentication', type='http', auth='user')
    def oauth2callback(self, **kw):
        """Handle Microsoft OAuth2 redirect callback and obtain tokens."""
        if 'error' in kw:
            _logger.error(
                "OneDrive OAuth error: %s - %s",
                kw.get('error'),
                kw.get('error_description'),
            )
            return request.redirect('/web')

        code = kw.get('code')
        state_raw = kw.get('state')
        if not code or not state_raw:
            return request.redirect('/web')

        try:
            state = json.loads(state_raw)
        except (ValueError, TypeError):
            state = {}

        dashboard_pool = request.env['onedrive.dashboard']
        dashboard_pool.check_access('create')
        dashboard_pool.get_tokens(code)

        url_return = state.get('url_return', '/web')
        parsed = urlparse(url_return)
        # Ensure url_return is a safe local relative URL to prevent open redirect
        if parsed.netloc or not url_return.startswith('/'):
            url_return = '/web'

        return request.redirect(url_return)

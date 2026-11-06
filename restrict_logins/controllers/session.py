# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
from urllib.parse import urlencode

from werkzeug.exceptions import Forbidden

from odoo import SUPERUSER_ID, api, http
from odoo.addons.web.controllers.session import Session as WebSession
from odoo.exceptions import AccessDenied
from odoo.http import request

from ..utils import (
    clear_all_session_files, clear_session_history, writable_cursor)


class Session(WebSession):
    """Handles the logout of the user, of the other devices of the user and
    the forced logout of every user."""

    @http.route()
    def logout(self, redirect='/odoo'):
        """Clear the session details of the user, then log out."""
        uid = request.session.uid
        if uid:
            with writable_cursor(request.env) as cursor:
                env = api.Environment(cursor, SUPERUSER_ID, {})
                env['res.users'].browse(uid)._clear_session()
        return super().logout(redirect=redirect)

    @http.route('/clear_all_sessions', type='http', auth='none',
                methods=['POST'], readonly=False)
    def logout_all(self, login=None, password=None, redirect='/odoo', **kw):
        """Log the user out of the other devices. The user has to prove the
        ownership of the account with the login and the password."""
        users = request.env['res.users']
        try:
            user = users._check_password_login(login, password)
        except AccessDenied:
            return request.redirect('/web/login?error=denied', 303)
        if user.sid and not clear_session_history(user.sid):
            return request.redirect('/web/login?error=denied', 303)
        user._clear_session()
        request.session.logout(keep_db=True)
        params = {'login': login}
        if redirect.startswith('/') and not redirect.startswith('//'):
            params['redirect'] = redirect
        return request.redirect('/web/login?' + urlencode(params), 303)

    @http.route('/super/logout_all', type='http', auth='user',
                methods=['POST'], readonly=False)
    def super_logout_all(self, redirect='/odoo', **kw):
        """Log every user out. Only the administrators can do it."""
        if not request.env.user._is_admin():
            raise Forbidden()
        clear_all_session_files()
        request.env['res.users'].sudo().search(
            ['|', ('sid', '!=', False), ('logged_in', '=', True)]
        )._clear_session()
        request.session.logout(keep_db=True)
        return request.redirect(redirect, 303)

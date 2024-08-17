# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import os
from odoo.addons.web.controllers.session import Session as WebSession
import odoo
import odoo.modules.registry
from odoo import http
from odoo.http import request
from odoo.tools._vendor import sessions


# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'}
LOGIN_SUCCESSFUL_PARAMS = set()


def clear_session_history(u_sid, f_uid=False):
    """ Clear all the user session histories of a particular user """
    path = odoo.tools.config.session_dir
    store = odoo.http.FilesystemSessionStore(
        path, session_class=odoo.http.Session, renew_missing=True)
    session_path = store.get_session_filename(u_sid)
    try:
        os.remove(session_path)
        return True
    except OSError as e:
        pass
    return False


def super_clear_all():
    """ Clear all the user session histories """
    path = odoo.tools.config.session_dir
    store = sessions.FilesystemSessionStore(
        path, session_class=odoo.http.Session, renew_missing=True)
    for fname in os.listdir(store.path):
        path = os.path.join(store.path, fname)
        try:
            os.unlink(path)
        except OSError:
            pass
    return True


class Session(WebSession):
    """
    This class includes methods to handle user logouts, clear individual user
    sessions, and perform a force logout, which logs out from all devices.
    """
    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        """ Logs out the current user by clearing their session. """
        user = request.env['res.users'].with_user(1).search(
            [('id', '=', request.session.uid)])
        user._clear_session()  # Clear user session
        request.session.logout(keep_db=True)
        return request.redirect(redirect, 303)

    @http.route('/clear_all_sessions', type='http', auth="none")
    def logout_all(self, redirect='/web', f_uid=False):
        """ Log out from all the sessions of the current user """
        if f_uid:
            user = request.env['res.users'].with_user(1).browse(int(f_uid))
            if user:
                # Clear session file for the user
                session_cleared = clear_session_history(user.sid, f_uid)
                if session_cleared:
                    # Clear user session
                    user._clear_session()
        request.session.logout(keep_db=True)
        return request.redirect(redirect, 303)

    @http.route('/super/logout_all', type='http', auth="none")
    def super_logout_all(self, redirect='/web'):
        """ Log out from all the sessions of all users. """
        users = request.env['res.users'].with_user(1).search([])
        for user in users:
            # Clear session file for the user
            session_cleared = super_clear_all()
            if session_cleared:
                user._clear_session()  # Clear user session
        request.session.logout(keep_db=True)
        return request.redirect(redirect, 303)

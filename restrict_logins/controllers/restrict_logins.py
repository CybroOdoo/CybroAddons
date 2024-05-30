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
import werkzeug
import werkzeug.exceptions
import werkzeug.routing
from odoo.addons.web.controllers import main
import odoo
import odoo.modules.registry
from odoo import SUPERUSER_ID
from odoo import http
from odoo.http import request
from odoo.tools._vendor import sessions
from odoo.tools.translate import _


def clear_session_history(u_sid, f_uid=False):
    """ Clear all the user session histories of a particular user """
    path = odoo.tools.config.session_dir
    store = sessions.FilesystemSessionStore(
        path, session_class=odoo.http.OpenERPSession, renew_missing=True)
    session_fname = store.get_session_filename(u_sid)
    try:
        os.remove(session_fname)
        return True
    except OSError:
        pass
    return False


def super_clear_all():
    """ Clear all the user session histories """
    path = odoo.tools.config.session_dir
    store = sessions.FilesystemSessionStore(
        path, session_class=odoo.http.OpenERPSession, renew_missing=True)
    for fname in os.listdir(store.path):
        path = os.path.join(store.path, fname)
        try:
            os.unlink(path)
        except OSError:
            pass
    return True


class Session(main.Session):
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
        return werkzeug.utils.redirect(redirect, 303)

    @http.route('/clear_all_sessions', type='http', auth="none")
    def logout_all(self, redirect='/web', f_uid=False):
        """ Log out from all the sessions of the current user """
        if f_uid:
            user = request.env['res.users'].with_user(1).browse(int(f_uid))
            if user:
                # Clear session file for the user
                session_cleared = clear_session_history(user.sid, f_uid)
                if session_cleared:
                    user._clear_session()  # Clear user session
        request.session.logout(keep_db=True)
        return werkzeug.utils.redirect(redirect, 303)

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
        return werkzeug.utils.redirect(redirect, 303)


class Home(main.Home):
    """ This class includes methods related to user authentication and login."""
    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        """ Handle user login through the web interface. """
        main.ensure_db()
        request.params['login_success'] = False
        if (request.httprequest.method == 'GET' and redirect and
                request.session.uid):
            return request.redirect(redirect)
        if not request.uid:
            request.uid = odoo.SUPERUSER_ID
        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                uid = request.session.authenticate(request.session.db,
                                                   request.params['login'],
                                                   request.params['password'])
                request.params['login_success'] = True
                return request.redirect(
                    self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                failed_uid = request.uid
                request.uid = old_uid
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                elif e.args[0] == "already_logged_in":
                    values['error'] = "User already logged in. Log out from " \
                                      "other devices and try again."
                    values['logout_all'] = True
                    values[
                        'failed_uid'] = failed_uid if (
                            failed_uid != SUPERUSER_ID) else False
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get(
                    'error') == 'access':
                values['error'] = _('Only employee can access this database. '
                                    'Please contact the administrator.')
        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')
        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True
        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import odoo
from odoo import http
from odoo.addons.web.controllers import home
from odoo.addons.web.controllers.utils import ensure_db
from odoo.http import request, route
from odoo.tools.translate import _
from odoo.exceptions import AccessDenied
# reuse helpers from session module
from .session import _check_user_ip, _get_client_ip

SIGN_UP_REQUEST_PARAMS = {
    'db', 'login', 'debug', 'token', 'message', 'error',
    'scope', 'mode', 'redirect', 'redirect_hostname', 'email',
    'name', 'partner_id', 'password', 'confirm_password', 'city',
    'country_id', 'lang', 'signup_email'
}
CREDENTIAL_PARAMS = ['login', 'password', 'type']


class Home(home.Home):
    """Custom Home controller that enforces IP restriction on web login."""

    @route('/web/login', type='http', auth="none", methods=['GET', 'POST'], csrf=False)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False

        # If already logged in, and GET with redirect, go there
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        # prepare env for public
        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)

        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid

            # get client ip in a proxy-safe way
            ip_address = _get_client_ip(request)
            login = request.params.get('login')
            password = request.params.get('password')

            if login and password:
                user = request.env['res.users'].sudo().search([('login', '=', login)], limit=1)

                try:
                    # check IP restriction
                    _check_user_ip(user, ip_address)

                    # collect credentials dict
                    credential = {k: v for k, v in request.params.items() if k in CREDENTIAL_PARAMS}
                    credential.setdefault('type', 'password')

                    auth_info = request.session.authenticate(request.db, credential)
                    uid = auth_info.get('uid')

                    # successful login, redirect
                    request.params['login_success'] = True
                    return request.redirect(self._login_redirect(uid, redirect=redirect))

                except AccessDenied as e:
                    request.update_env(user=old_uid)
                    values['error'] = str(e) if str(e) else _("Not allowed to login from this IP")
                except odoo.exceptions.AccessDenied as e:
                    request.update_env(user=old_uid)
                    # generic wrong credentials message
                    values['error'] = _("Wrong login/password") if e.args == odoo.exceptions.AccessDenied().args else e.args[0]

        else:
            if request.params.get('error') == 'access':
                values['error'] = _(
                    'Only employees can access this database. Please contact the administrator.'
                )

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')
        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response
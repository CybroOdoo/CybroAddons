# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Niyas Raphy(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.addons.web.controllers import home
from odoo.http import request
from odoo.exceptions import Warning
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url, is_user_internal

SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'}


class Home(home.Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        # simulate hybrid auth=user/auth=public, despite using auth=none to be able
        # to redirect users when no db is selected - cfr ensure_db()
        if request.env.uid is None:
            if request.session.uid is None:
                # no user -> auth=public with specific website public user
                request.env["ir.http"]._auth_method_public()
            else:
                # auth=user
                request.update_env(user=request.session.uid)

        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        if request.httprequest.method == 'POST':
            old_uid = request.uid
            ip_address = request.httprequest.environ['REMOTE_ADDR']
            if request.params['login']:
                user_rec = request.env['res.users'].sudo().search(
                    [('login', '=', request.params['login'])])
                if user_rec.allowed_ips:
                    ip_list = []
                    for rec in user_rec.allowed_ips:
                        ip_list.append(rec.ip_address)
                    if ip_address in ip_list:
                        try:
                            uid = request.session.authenticate(
                                request.session.db, request.params['login'],
                                request.params['password'])
                            request.params['login_success'] = True
                            return request.redirect(
                                self._login_redirect(uid, redirect=redirect))
                        except odoo.exceptions.AccessDenied as e:
                            request.update_env = old_uid
                            if e.args == odoo.exceptions.AccessDenied().args:
                                values['error'] = _("Wrong login/password")
                    else:
                        request.update_env = old_uid
                        values['error'] = _("Not allowed to login from this IP")
                else:
                    try:
                        uid = request.session.authenticate(request.session.db,
                                                           request.params[
                                                               'login'],
                                                           request.params[
                                                               'password'])
                        request.params['login_success'] = True
                        return request.redirect(
                            self._login_redirect(uid, redirect=redirect))
                    except odoo.exceptions.AccessDenied as e:
                        request.update_env = old_uid
                        if e.args == odoo.exceptions.AccessDenied().args:
                            values['error'] = _("Wrong login/password")
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

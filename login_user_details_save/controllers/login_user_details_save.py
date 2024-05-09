# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import odoo
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.web.controllers.home import Home as Home
from odoo.addons.web.controllers.session import Session
from odoo.addons.web.controllers.utils import ensure_db

# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error',
                          'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name',
                          'partner_id',
                          'password', 'confirm_password', 'city', 'country_id',
                          'lang'}


class SessionWebsite(Session):
    """Extended session controller for website-related operation"""

    @http.route('/web/session/logout_popup', type='http', auth="public",
                website=True)
    def logout_popup(self):
        """Render the logout popup template"""
        login_details = request.env['logout.popup'].search(
            [('user_id', '=', int(request.uid))])
        values = {
            'login_details': login_details.save_details if login_details
            else False
        }
        return request.render('login_user_details_save.logout_popup_template',
                              values)

    @http.route('/web/session/save_logout', type='http', auth="public",
                website=True, csrf=False)
    def save_logout_details(self, **post):
        """Save user details when 'save login details' checkbox is checked"""
        login_name = request.env.user.login
        logout_details_obj = request.env['logout.popup']
        record = logout_details_obj.search(
            [('user_id', '=', request.uid)])
        if post.get('rememberMeCheckbox') and not record:
            logout_details_obj.create({
                'name': login_name,
                'save_details': True,
                'user_id': request.uid
            })
        if record and not post.get('rememberMeCheckbox'):
            record.unlink()
        return request.redirect('/web/session/logout')


class WebHome(Home):
    """Extended Home controller for login-related operations"""

    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'] = False

        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        # simulate hybrid auth=user/auth=public, despite using auth=none to be able
        # to redirect users when no db is selected - cfr ensure_db()
        if not request.uid:
            public_user = request.env.ref('base.public_user')
            request.update_env(user=public_user.id)
        values = {k: v for k, v in request.params.items() if
                  k in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None
        if request.httprequest.method == 'POST':
            try:
                uid = request.session.authenticate(request.db,
                                                   request.params['login'],
                                                   request.params['password'])
                request.params['login_success'] = True
                return request.redirect(
                    self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get(
                    'error') == 'access':
                values['error'] = _(
                    'Only employees can access this database. Please contact the administrator.')
        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True
        conf_param = request.env['ir.config_parameter'].sudo()
        base_url = conf_param.get_param('web.base.url')
        log_data_list = []
        for log_data in request.env['logout.popup'].search([]):
            log_data_list.append([log_data.name, base_url +
                                  '/web/image?' +
                                  'model=res.users&id=' +
                                  str(log_data.user_id.id) +
                                  '&field=image_1920', log_data.user_id.name])
        values['login_data'] = log_data_list
        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

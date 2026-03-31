# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (<https://www.cybrosys.com>)
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
import hashlib
import odoo
from odoo import http
from odoo.tools import pycompat
from odoo.http import request
from odoo.addons.web.controllers.home import Home as WebHome
from odoo.addons.web.controllers.utils import ensure_db
from odoo.tools.translate import _, LazyTranslate

_lt = LazyTranslate(__name__)

# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error',
                          'scope', 'mode', 'redirect', 'redirect_hostname',
                          'email', 'name', 'partner_id', 'password',
                          'confirm_password', 'city', 'country_id', 'lang'}

CREDENTIAL_PARAMS = ['login', 'password', 'type']


class Home(WebHome):
    @http.route('/web/login', type='http', auth='none', readonly=False,
                list_as_website_content=_lt("Login"))
    def web_login(self, redirect=None, **kw):
        """
            Handle web login requests and render a customized login page.

                This method extends the default Odoo web login flow by:
                - Handling authentication for GET and POST requests
                - Managing public and authenticated user environments
                - Supporting captcha verification when required
                - Displaying appropriate error messages on login failure
                - Dynamically applying login page styles based on system
                  configuration parameters (orientation, background color,
                  background image, or background URL)

                Depending on the configured orientation, a custom login template
                is rendered; otherwise, the default Odoo login page is used.

                :param str redirect: Optional URL to redirect the user after
                                     successful authentication
                :param dict kw: Additional request parameters
                :return: HTTP response rendering the login page or redirecting
                         after successful login
                :rtype: werkzeug.wrappers.Response
        """
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

        values = {k: v for k, v in request.params.items() if
                  k in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            try:
                credential = {key: value for key, value in
                              request.params.items() if
                              key in CREDENTIAL_PARAMS and value}
                credential.setdefault('type', 'password')
                if request.env['res.users']._should_captcha_login(credential):
                    request.env['ir.http']._verify_request_recaptcha_token(
                        'login')
                auth_info = request.session.authenticate(request.env,
                                                         credential)
                request.params['login_success'] = True
                return request.redirect(
                    self._login_redirect(auth_info['uid'], redirect=redirect))
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
        orientation = conf_param.get_param('web_login_styles.orientation')
        image = conf_param.get_param('web_login_styles.image')
        url = conf_param.get_param('web_login_styles.url')
        background_type = conf_param.get_param('web_login_styles.background')
        if orientation:
            values['orientation'] = orientation
        if background_type == 'color':
            values['bg'] = ''
            values['color'] = conf_param.sudo().get_param(
                'web_login_styles.color')
        elif background_type == 'image':
            exist_rec = request.env['ir.attachment'].sudo().search(
                [('is_background', '=', True)])
            if exist_rec:
                exist_rec.unlink()
            attachments = request.env['ir.attachment'].sudo().create({
                'name': 'Background Image',
                'datas': image,
                'type': 'binary',
                'mimetype': 'image/png',
                'public': True,
                'is_background': True
            })
            base_url = conf_param.sudo().get_param('web.base.url')
            url = base_url + '/web/image?' + 'model=ir.attachment&id=' + str(
                attachments.id) + '&field=datas'
            values['bg_img'] = url or ''
        elif background_type == 'url':
            pre_exist = request.env['ir.attachment'].sudo().search(
                [('url', '=', url)])
            if not pre_exist:
                attachments = request.env['ir.attachment'].sudo().create({
                    'name': 'Background Image URL',
                    'url': url,
                    'type': 'url',
                    'public': True
                })
            else:
                attachments = pre_exist
            encode = hashlib.md5(
                (attachments.url or "").encode("utf-8")
            ).hexdigest()[:7]
            encode_url = "/web/image/{}-{}".format(attachments.id, encode)
            values['bg_img'] = encode_url or ''
        if orientation == 'right':
            response = request.render('web_login_styles.login_template_right',
                                      values)
        elif orientation == 'left':
            response = request.render('web_login_styles.login_template_left',
                                      values)
        elif orientation == 'middle':
            response = request.render('web_login_styles.login_template_middle',
                                      values)
        else:
            response = request.render('web.login', values)

        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

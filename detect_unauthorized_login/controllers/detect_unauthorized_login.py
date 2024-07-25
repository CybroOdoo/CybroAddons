# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Afra MP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
import base64
import cv2
import datetime
import logging
import odoo
import odoo.modules.registry
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.web.controllers.home import Home

_logger = logging.getLogger(__name__)
# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error',
                          'scope', 'mode', 'redirect', 'redirect_hostname',
                          'email', 'name', 'partner_id', 'password',
                          'confirm_password', 'city', 'country_id', 'lang',
                          'signup_email'}
LOGIN_SUCCESSFUL_PARAMS = set()


class WrongPassword(Home):
    """While entering wrong password create an error and send mail to the user and also capture the image of
    unauthorized user"""

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        """While entering wrong password an error message is created,
        capture the image of user, and send a notification
        to authorized user"""
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)
        # simulate hybrid auth=user/auth=public, despite using auth=none to
        # be able to redirect users when no db is selected - cfr ensure_db()
        if request.env.uid is None:
            if request.session.uid is None:
                # no user -> auth=public with specific website public user
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)
        values = {k: v for k, v in request.params.items()
                  if k in SIGN_UP_REQUEST_PARAMS}
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
                return request.redirect(self._login_redirect(uid,
                                                             redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                    try:
                        # Capture an image
                        cap = cv2.VideoCapture(0)
                        ret, frame = cap.read()
                        ret, jpeg_image = cv2.imencode('.jpg', frame)
                        base64_image = base64.b64encode(jpeg_image)
                        cap.release()
                    except:
                        capture = request.env['auto.capture'].sudo().create({
                            'email': request.params['login'],
                            'date': datetime.datetime.now(),
                        })
                        User = request.env['res.users']
                        user_sudo = User.sudo().search(
                            User._get_login_domain(request.params['login']),
                            order=User._get_login_order(), limit=1
                        )
                        template = request.env.ref(
                            'detect_unauthorized_login'
                            '.email_template_cant_access_camera').with_context(
                            user=user_sudo.name)
                        template.sudo().send_mail(capture.id, force_send=True)
                    else:
                        capture = request.env['auto.capture'].sudo().create({
                            'email': request.params['login'],
                            'date': datetime.datetime.now(),
                            'image': base64_image,
                        })
                        User = request.env['res.users']
                        user_sudo = User.sudo().search(
                            User._get_login_domain(request.params['login']),
                            order=User._get_login_order(), limit=1
                        )
                        template = request.env.ref(
                            'detect_unauthorized_login'
                            '.email_template_wrong_password').with_context(
                            user=user_sudo.name)
                        template.sudo().send_mail(capture.id, force_send=True)
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get(
                    'error') == 'access':
                values['error'] = _(
                    'Only employees can access this database. '
                    'Please contact the administrator.')
        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')
        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True
        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

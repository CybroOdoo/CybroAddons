# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import datetime
import logging
import odoo
from odoo import http
from odoo.http import request
import subprocess
import sys
from odoo.addons.web.controllers.home import Home

_logger = logging.getLogger(__name__)
# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error',
                          'scope', 'mode', 'redirect', 'redirect_hostname',
                          'email', 'name', 'partner_id', 'password',
                          'confirm_password', 'city', 'country_id', 'lang',
                          'signup_email'}


class WrongPassword(Home):
    """Captures an image and notifies the user upon failed login attempts."""

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        """Handle login attempts, capturing an image and notifying the user if the password is incorrect."""
        request.params['login_success'] = False

        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)

        values = {key: value for key, value in request.params.items()
                  if key in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            try:
                # ✅ FIXED authenticate call
                uid = request.session.authenticate(request.env,
                                                   {'login': request.params[
                                                       'login'],
                                                    'password': request.params[
                                                        'password'],
                                                    'type': 'password'})
                request.params['login_success'] = True
                return request.redirect(self._login_redirect(uid, redirect=redirect))

            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = request.env._("Wrong login/password")
                    
                    # Fetch the actual user to get their configured email address
                    user_sudo = request.env['res.users'].sudo().search(
                        request.env['res.users']._get_login_domain(request.params['login']),
                        order=request.env['res.users']._get_login_order(),
                        limit=1
                    )
                    target_email = user_sudo.email if user_sudo and user_sudo.email else request.params['login']
                    target_name = user_sudo.name if user_sudo else request.params['login']
                    
                    try:
                        
                        python_code = """
import cv2
import base64
import sys
import time

try:
    for index in [0, 1, 2, 3, -1]:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # Warm up the camera sensor (crucial for many webcams)
            for _ in range(5):
                cap.read()
                time.sleep(0.1)
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                ret, jpeg_image = cv2.imencode('.jpg', frame)
                if ret:
                    print(base64.b64encode(jpeg_image).decode('utf-8'))
                    sys.exit(0)
except Exception as e:
    print('Subprocess Exception:', e, file=sys.stderr)
sys.exit(1)
"""
                        result = subprocess.run(
                            [sys.executable, "-c", python_code],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode != 0:
                            _logger.warning("Camera capture subprocess failed with return code %s. Stderr: %s", result.returncode, result.stderr)
                            raise Exception("Failed to capture image in subprocess")
                        base64_image = result.stdout.strip().encode('utf-8')
                        if not base64_image:
                            raise Exception('Subprocess returned empty image data')
                        _logger.info('Captured image from subprocess, size %d bytes', len(base64_image))
                    except Exception as ex:
                        _logger.warning("Camera capture failed: %s", ex)
                        capture = request.env['auto.capture'].sudo().create({
                            'email': target_email,
                            'date': datetime.datetime.now(),
                        })
                        template = request.env.ref(
                            'detect_unauthorized_login.mail_template_cant_access_camera'
                        ).with_context(user=target_name)
                        template.sudo().send_mail(capture.id, force_send=True)
                    else:
                        capture = request.env['auto.capture'].sudo().create({
                            'email': target_email,
                            'date': datetime.datetime.now(),
                            'image': base64_image,
                        })
                        template = request.env.ref(
                            'detect_unauthorized_login.mail_template_wrong_password'
                        ).with_context(user=target_name)
                        template.sudo().send_mail(capture.id, force_send=True)
                else:
                    values['error'] = e.args[0]

        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = request.env._(
                    'Only employees can access this database. '
                    'Please contact the administrator.'
                )

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

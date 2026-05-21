# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V  (odoo@cybrosys.com)
#
#   This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import math
import random
import string
from odoo import fields, http
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.portal.controllers.web import Home


def generate_otp():
    """Generate a 6-digit OTP (One-Time Password)."""
    digits = "0123456789"
    otp = ""
    for i in range(6):
        otp += digits[int(math.floor(random.random() * 10))]
    return otp


def generate_user_uid():
    """Generate a unique identifier for a user."""
    values = string.ascii_letters + string.digits
    user_uid = ""
    for i in range(64):
        user_uid += values[int(math.floor(random.random() * len(values)))]
    exist = request.env['res.users.activity'].sudo().search(
        [('user_uid', '=', user_uid)])
    if exist:
        generate_user_uid()
    return user_uid


class Suspicious(Home):
    """Controller for handling suspicious login behavior."""
    @http.route('/web/login/send_otp', type="json", auth="public")
    def send_otp(self, vals):
        """Send OTP to the user for login. Returns True if login and password
        are correct; otherwise, returns False
        """
        try:
            db = request.session.db
            uid = request.session.authenticate(db, vals['login'],
                                               vals['password'])
            user = request.env['res.users'].browse(uid).sudo()
            otp = user.otp = generate_otp()
            template = request.env.ref(
                'suspicious_login.suspicious_email_template')
            context = {
                'user': user,
                'otp': otp
            }
            company = user.company_id
            mail_body = request.env['ir.qweb']._render(template.id, context)
            mail_values = {
                'subject': f'{company.name}: New OTP for login',
                'email_from': f'{company.email_formatted}',
                'author_id': user.partner_id.id,
                'email_to': user.partner_id.email,
                'body_html': mail_body,
            }
            http.request.env['mail.mail'].sudo().create(mail_values).send()
            request.session.logout()
            request.session.db = db
            return True
        except AccessDenied:
            user = request.env['res.users'].sudo().search(
                [('login', '=', vals['login'])])
            if user:
                request.env['res.users.login.attempt'].sudo().create({
                    'user_id': user.id,
                    'login_time': fields.Datetime.now(),
                    'failed_reason': 'Wrong Login or Password',
                    'status': 'failed',
                    'ip_address': vals['ip_address'],
                    'location': vals['location'],
                    'timezone': vals['timezone'],
                    'platform': vals['platform'],
                    'browser': vals['browser'],
                })
            return False

    @http.route('/web/login/check_otp', type="json", auth="public")
    def check_otp(self, vals):
        """Check the OTP that the user inputs with the OTP sent through email.
        Returns the status and redirect link.
        """
        try:
            uid = request.session.authenticate(request.session.db,
                                               vals['login'], vals['password'])
            user = request.env['res.users'].browse(uid).sudo()
            if user.otp == vals['otp']:
                result = {
                    'success': True,
                    'redirect': self._login_redirect(uid) + vals.get(
                        'redirect')
                }
                user.otp = generate_otp()
                request.env['res.users.login.attempt'].sudo().create({
                    'user_id': request.env.user.id,
                    'login_time': fields.Datetime.now(),
                    'status': 'success',
                    'ip_address': vals['ip_address'],
                    'location': vals['location'],
                    'timezone': vals['timezone'],
                    'platform': vals['platform'],
                    'browser': vals['browser'],
                })
                if vals['is_trusted']:
                    act_obj = request.env['res.users.activity'].sudo()
                    activity = act_obj.search([
                        ('user_id', '=', user.id)
                    ])
                    if activity:
                        result.update({
                            'uuid': activity.user_uid
                        })
                    else:
                        uuid = generate_user_uid()
                        act_obj.create({
                            'user_id': user.id,
                            'user_uid': uuid
                        })
                        result.update({
                            'uuid': uuid
                        })
                return result
            else:
                db = request.session.db
                request.env['res.users.login.attempt'].sudo().create({
                    'user_id': request.env.user.id,
                    'login_time': fields.Datetime.now(),
                    'failed_reason': 'Wrong OTP',
                    'status': 'failed',
                    'ip_address': vals['ip_address'],
                    'location': vals['location'],
                    'timezone': vals['timezone'],
                    'platform': vals['platform'],
                    'browser': vals['browser'],
                })
                request.session.logout()
                request.session.db = db
                return {
                    'success': False
                }
        except AccessDenied:
            user = request.env['res.users'].sudo().search(
                [('login', '=', vals['login'])])
            if user:
                request.env['res.users.login.attempt'].sudo().create({
                    'user_id': user.id,
                    'login_time': fields.Datetime.now(),
                    'failed_reason': 'Wrong Login or Password',
                    'status': 'failed',
                    'ip_address': vals['ip_address'],
                    'location': vals['location'],
                    'timezone': vals['timezone'],
                    'platform': vals['platform'],
                    'browser': vals['browser'],
                })
            return {
                'success': False
            }

    @http.route('/web/login/check_uuid', type="json", auth="public")
    def check_uuid(self, vals):
        """Check the UUID with the user's UUID if the browser has one.
        Returns True if the user's UUID matches with the browser's UUID.
        """
        try:
            uid = request.session.authenticate(request.session.db,
                                               vals['login'], vals['password'])
            user = request.env['res.users'].browse(uid)
            act_obj = request.env['res.users.activity'].sudo()
            activity = act_obj.search([
                ('user_id', '=', user.id)
            ])
            if activity.user_uid == vals['uuid']:
                result = {
                    'success': True,
                    'redirect': self._login_redirect(uid) + vals.get(
                        'redirect')
                }
                request.env['res.users.login.attempt'].sudo().create({
                    'user_id': request.env.user.id,
                    'login_time': fields.Datetime.now(),
                    'status': 'success',
                    'ip_address': vals['ip_address'],
                    'location': vals['location'],
                    'timezone': vals['timezone'],
                    'platform': vals['platform'],
                    'browser': vals['browser'],
                })
                return result
            else:
                return {
                    'success': False
                }
        except AccessDenied:
            return {
                'success': False
            }

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Controllers for mobile signup with Twilio OTP verification."""
import logging
import secrets
import time
import werkzeug.exceptions
from twilio.rest import Client
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.auth_signup.controllers.main import (
    AuthSignupHome as AuthSignupHomeBase,
)
from odoo.addons.mail.tools.discuss import get_twilio_credentials
from odoo.addons.auth_signup.models.res_users import SignupError

_logger = logging.getLogger(__name__)


class AuthSignupHome(AuthSignupHomeBase):
    """Allow users to signup with mobile number verified via Twilio OTP."""

    def _verify_signup_otp(self, full_mobile, kw):
        """Verify the OTP stored in the session against the form submission."""
        session_otp = request.session.get('signup_otp')
        submitted_otp = (kw.get('sms_otp') or '').strip()

        if not session_otp:
            return request.env._(
                "Please request a verification code before signing up.")
        if time.time() - session_otp.get('timestamp', 0) > 120:
            return request.env._(
                "Verification code has expired. Please request a new code.")
        if session_otp.get('mobile') != full_mobile:
            return request.env._(
                "The mobile number does not match the one used to request "
                "the verification code.")
        if submitted_otp != str(session_otp.get('otp')):
            return request.env._(
                "Invalid verification code. Please check and try again.")
        return None

    @http.route('/web/signup-mobile', type='http', auth='public',
                website=True, sitemap=False)
    def web_auth_signup_mobile(self, *args, **kw):
        """Create new user with mobile number after OTP verification."""
        qcontext = self.get_auth_signup_qcontext()
        country_code = (kw.get('country_code') or '').strip().lstrip('+')
        mobile_number = (kw.get('login_mobile') or '').strip()
        login_val = (
            f"+{country_code}{mobile_number}"
            if country_code and mobile_number
            else ''
        )
        if login_val:
            qcontext.update({'login': login_val})
            kw.update({'login': login_val})

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if request.httprequest.method == 'POST':
            otp_error = self._verify_signup_otp(login_val, kw)
            if otp_error:
                qcontext['error'] = otp_error
            else:
                try:
                    self.do_signup(qcontext, False)
                    request.session.pop('signup_otp', None)
                    user = request.env['res.users'].sudo().search(
                        [('login', '=', qcontext['login'])], limit=1)
                    if user.partner_id and kw.get('signup_mobile'):
                        user.partner_id.update({'phone': qcontext['login']})
                    return self.web_login(*args, **kw)
                except UserError as err:
                    qcontext['error'] = err.args[0]
                except (SignupError, AssertionError):
                    if request.env["res.users"].sudo().search_count(
                            [("login", "=", qcontext.get("login"))]):
                        qcontext["error"] = request.env._(
                            "Another user is already registered "
                            "using this Mobile Number.")
                    else:
                        _logger.error("Signup failed for mobile registration")
                        qcontext['error'] = request.env._(
                            "Could not create a new account.")

        response = request.render('signup_with_twilio.signup_mobile', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    @http.route('/web/login', type='http', auth="public", sitemap=False)
    def web_login(self, *args, **kw):
        """Update parameters to login with mobile number."""
        if kw.get('login'):
            request.params.update({'login': kw.get('login')})
        return super().web_login(*args, **kw)

    @http.route('/web/send_otp', auth='public', type='jsonrpc')
    def web_send_otp(self, **kw):
        """Send OTP through SMS to the given number using Twilio."""
        country_code = str(kw.get('country_code') or '').strip().lstrip('+')
        mobile = str(kw.get('mobile') or '').strip()

        if not country_code.isdigit() or not mobile.isdigit():
            raise UserError(request.env._(
                "Please provide a valid mobile number and country code."))

        full_mobile = f"+{country_code}{mobile}"

        last_sent = request.session.get('signup_otp_last_sent', 0)
        current_time = time.time()
        if current_time - last_sent < 30:
            raise UserError(request.env._(
                "Please wait a moment before requesting another verification "
                "code."))

        (account_sid, auth_token) = get_twilio_credentials(request.env)
        from_number = request.env['ir.config_parameter'].sudo().get_str(
            'signup_with_twilio.twilio_from_number')
        if not account_sid or not auth_token or not from_number:
            raise UserError(request.env._('Twilio credentials are required.'))

        otp = f"{secrets.randbelow(10000):04d}"

        request.session['signup_otp'] = {
            'otp': otp,
            'mobile': full_mobile,
            'timestamp': current_time,
        }
        request.session['signup_otp_last_sent'] = current_time

        client = Client(account_sid, auth_token)
        sms_body = request.env._(
            "Your verification code is: %s. This code is valid for 2 "
            "minutes.",
            otp,
        )
        message = client.messages.create(
            to=full_mobile,
            from_=from_number,
            body=sms_body,
        )
        _logger.info(
            "Twilio OTP SMS sent successfully (Message SID: %s)", message.sid)
        return {
            'status': 'success',
            'message': request.env._('Verification code sent successfully.'),
        }

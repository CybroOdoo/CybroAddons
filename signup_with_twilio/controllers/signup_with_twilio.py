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
import logging
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from twilio.rest import Client
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.web.controllers.home import Home
from odoo.addons.mail.tools.discuss import get_twilio_credentials
from odoo.addons.auth_signup.models.res_users import SignupError
_logger = logging.getLogger(__name__)


class AuthSignupHome(Home):
    """Uses to signup with mobile number and
    login with the same mobile number"""

    @http.route('/web/signup-mobile', type='http', auth='public',
                website=True, sitemap=False)
    def web_auth_signup_mobile(self, *args, **kw):
        """Create new user with mobile number"""
        qcontext = self.get_auth_signup_qcontext()
        if kw.get('country_code') and kw.get('login_mobile'):
            qcontext.update({'login': kw.get('country_code') + kw.get(
                'login_mobile')})
            kw.update({'login': kw.get('country_code') + kw.get(
                'login_mobile')})
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                user = request.env['res.users'].sudo().search(
                    [('login', '=', qcontext['login'])])
                if user.partner_id and kw.get('signup_mobile'):
                    user.partner_id.update({'email': ''})
                    user.partner_id.update({'phone': qcontext['login']})
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search(
                        [("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _(
                        "Another user is already registered "
                        "using this Mobile Number.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")
        response = request.render('signup_with_twilio.signup_mobile', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    @http.route('/web/login', type='http', auth="public", website=True)
    def web_login(self, redirect=None, **kw):
        """Update the parameters to login with mobile Number"""
        request.params.update({'login': kw.get('login')})
        return super().web_login(**kw)

    @http.route('/web/send_otp', auth='public', type='json')
    def web_send_otp(self, **kw):
        """Sent OTP through SMS to the given number using twilio"""
        (account_sid, auth_token) = get_twilio_credentials(request.env)
        from_number = request.env['ir.config_parameter'].sudo().get_param(
            'signup_with_twilio.twilio_from_number')
        if not account_sid or not auth_token or not from_number:
            raise UserError(_('Twilio Credential are Required'))
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            to='+' + kw.get('country_code') + kw.get('mobile'),
            from_=from_number,
            body='Your Odoo verification code is:' + str(kw.get('otp')) +
                 '.OTP valid till 2 minutes.'
        )
        _logger.info('Message successfully sent to your mobie number: %s',
                     message.sid)

    @http.route('/web/reset_password', type='http', auth='public',
                website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        """Update the email in user email field"""
        if kw.get('login-mail'):
            user = request.env['res.users'].sudo().search(
                [('login', '=', kw.get('login'))])
            if user:
                user.email = kw.get('login-mail')
        return super(AuthSignupHome, self).web_auth_reset_password(args, **kw)

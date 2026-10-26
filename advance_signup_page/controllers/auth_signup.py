# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
import logging
from urllib.parse import urlencode
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.home import ensure_db

_logger = logging.getLogger(__name__)


class AuthSignupHome(AuthSignupHome):
    """Custom AuthSignupHome Controller for Handling Signup. This custom
    AuthSignupHome controller extends the default Odoo 'AuthSignupHome'
    controller to handle signup functionality. It provides methods for web
    login and signup, including additional configuration fields."""

    def _get_signup_configuration(self):
        """Get the signup configuration for the current website or fallback."""
        website = getattr(request.env, 'website', None)
        website_id = website.id if website else False
        return (
            request.env['signup.configuration'].sudo().search(
                [('website_id', '=', website_id)], limit=1
            ) or request.env['signup.configuration'].sudo().search([], limit=1)
        )

    @http.route()
    def web_login(self, *args, **kw):
        """ Perform web login."""
        ensure_db()
        response = super().web_login(*args, **kw)
        if hasattr(response, 'qcontext') and response.qcontext is not None:
            response.qcontext.update(self.get_auth_signup_config())
            configuration = self._get_signup_configuration()
            if configuration and configuration.is_active:
                response.qcontext.update({
                    'configuration': configuration,
                    'hide_header': True,
                    'hide_footer': True,
                })
        if request.session.uid:
            if request.httprequest.method == 'GET' and request.params.get(
                    'redirect'):
                # Redirect if already logged in and redirect param is present
                return request.redirect(request.params.get('redirect'))
            # Add message for non-internal user account without redirect
            # if account was just created
            if response.location == '/web/login_successful' and kw.get(
                    'confirm_password'):
                return request.redirect_query('/web/login_successful',
                                              query={'account_created': True})
        return response

    @http.route('/web/signup', type='http', auth='public', website=True,
                sitemap=False)
    def web_auth_signup(self, *args, **kw):
        """Overridden the controller function to add the configuration into
        the qcontext"""
        qcontext = self.get_auth_signup_qcontext()
        configuration = self._get_signup_configuration()
        for key in kw:
            qcontext[key] = kw[key]
        if configuration and configuration.is_active:
            qcontext.update({
                'configuration': configuration,
                'hide_header': True,
                'hide_footer': True,
            })
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                user = request.env['res.users']
                user_sudo = user.sudo().search(
                    user._get_login_domain(qcontext.get('login')),
                    order=user._get_login_order(), limit=1
                )
                template = request.env.ref(
                    'auth_signup.mail_template_user_signup_account_created',
                    raise_if_not_found=False)
                if user_sudo and template:
                    template.sudo().send_mail(user_sudo.id, force_send=True)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search(
                        [("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = request.env._(
                        "Another user is already registered using this email "
                        "address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = request.env._("Could not create a new account.")
        elif 'signup_email' in qcontext:
            user = request.env['res.users'].sudo().search(
                [('email', '=', qcontext.get('signup_email')),
                 ('state', '!=', 'new')], limit=1)
            if user:
                return request.redirect('/web/login?%s' % urlencode(
                    {'login': user.login, 'redirect': '/web'}))
        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        """Pass configuration and layout flags to reset password page."""
        response = super().web_auth_reset_password(*args, **kw)
        if hasattr(response, 'qcontext') and response.qcontext is not None:
            configuration = self._get_signup_configuration()
            if configuration and configuration.is_active:
                response.qcontext.update({
                    'configuration': configuration,
                    'hide_header': True,
                    'hide_footer': True,
                })
        return response

    def _prepare_signup_values(self, qcontext, **kwargs):
        """Updated the values with newly added fields"""
        values = super()._prepare_signup_values(qcontext, **kwargs)
        configuration = self._get_signup_configuration()
        if configuration and configuration.is_active:
            for field in configuration.signup_field_ids:
                if field.field_id and field.field_id.name:
                    values[field.field_id.name] = qcontext.get(field.field_id.name)
        return values

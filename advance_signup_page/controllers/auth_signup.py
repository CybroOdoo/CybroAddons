# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amal Varghese, Jumana Jabin MP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from werkzeug.urls import url_encode
from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.home import ensure_db

_logger = logging.getLogger(__name__)


class AuthSignupHome(AuthSignupHome):
    """Custom AuthSignupHome Controller for Handling Signup.This custom
     AuthSignupHome controller extends the default Odoo 'AuthSignupHome'
     controller to handle signup functionality.It provides methods for web
      login and signup, including additional configuration fields."""
    @http.route()
    def web_login(self, *args, **kw):
        """ Perform web login."""
        ensure_db()
        response = super().web_login(*args, **kw)
        configuration = request.env['signup.configuration'].sudo().search([(
            'website_id', '=', request.website.id)], limit=1)
        response.qcontext.update(self.get_auth_signup_config())
        response.qcontext.update({
            'is_hide_footer': True if configuration.is_hide_footer else False
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
        configuration = request.env['signup.configuration'].sudo(). \
            search([('website_id', '=', request.website.id)], limit=1)
        for key in kw:
            qcontext[key] = kw[key]
        if configuration:
            qcontext.update({
                'configuration': configuration
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
                    qcontext["error"] = _(
                        "Another user is already registered using this email "
                        "address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")
        elif 'signup_email' in qcontext:
            user = request.env['res.users'].sudo().search(
                [('email', '=', qcontext.get('signup_email')),
                 ('state', '!=', 'new')], limit=1)
            if user:
                return request.redirect('/web/login?%s' % url_encode(
                    {'login': user.login, 'redirect': '/web'}))
        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    def _prepare_signup_values(self, qcontext):
        """Updated the values with newly added fields"""
        keys = ['login', 'name', 'password']
        configuration = request.env['signup.configuration'] \
            .sudo().search([], limit=1)
        for field in configuration.signup_field_ids:
            keys.append(field.field_id.name)
        values = {key: qcontext.get(key) for key in keys}
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_lang_codes = [code for code, _ in
                                request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang
        return values

    @http.route('/web/signup', type='http', auth="public", website=True,
                sitemap=False)
    def website_signup(self):
        """Perform website signup."""
        values = {}
        configuration_signup = request.env[
            'configuration.signup'].sudo().search([], limit=1)
        if configuration_signup.is_show_terms_conditions:
            values[
                'terms_and_conditions'] = configuration_signup \
                .terms_and_conditions
        return request.render(
            "advance_signup_portal.advance_signup_portal.fields", values)

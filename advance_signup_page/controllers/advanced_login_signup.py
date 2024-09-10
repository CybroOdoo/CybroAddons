# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import odoo
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.web.controllers.main import Home
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db

_logger = logging.getLogger(__name__)
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error',
                          'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name',
                          'partner_id',
                          'password', 'confirm_password', 'city', 'country_id',
                          'lang', 'signup_email'}
LOGIN_SUCCESSFUL_PARAMS = set()


class AdvancedLoginSignup(Home):
    """Custom AdvancedLoginSignup Controller for Handling Login and Signup.This custom AdvancedLoginSignup
    controller extends the default Odoo 'Home' controller to handle login and
     signup functionality.It provides methods for web login and signup."""

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        """Function to  Handle web login. """
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and \
                request.session.uid:
            return request.redirect(redirect)
        # Simulate hybrid auth=user/auth=public, despite using auth=none to be,
        # able to redirect users when no db is selected - cfr ensure_db()
        if request.env.uid is None:
            if request.session.uid is None:
                request.env["ir.http"]._auth_method_public()
            else:
                request.update_env(user=request.session.uid)
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
                    'Only employees can access this database. Please contact '
                    'the administrator.')
        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')
        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True
        values.update({
            'header': True,
            'footer': True,
            'signup_url': '/web/signup',
        })
        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        configuration = request.env['signup.configuration'].sudo().search([(
            'website_id', '=', request.website.id)], limit=1)
        response.qcontext.update(self.get_auth_signup_config())
        response.qcontext.update({
            'is_hide_footer': bool(configuration.is_hide_footer)
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
        values = super()._prepare_signup_values(qcontext)
        configuration = request.env['signup.configuration'].sudo().search([], limit=1)
        for field in configuration.signup_field_ids:
            field_name = field.field_id.name
            values[field_name] = qcontext.get(field_name)
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

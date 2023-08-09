# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana K P (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import re
from odoo import http, _
from odoo.addons.web.controllers.main import Home, ensure_db, \
    SIGN_UP_REQUEST_PARAMS
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from odoo.http import request


class PasswordSecurity(Home):
    """overriding the website signup controller"""
    @http.route('/web/signup', type='http', auth='public', website=True,
                sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        values = {key: qcontext.get(key) for key in ('login', 'name',
                                                     'password')}
        get_param = request.env['ir.config_parameter'].sudo().get_param
        config_strength = get_param('user_password_strength.is_strength')
        config_digit = get_param('user_password_strength.is_digit')
        config_upper = get_param('user_password_strength.is_upper')
        config_lower = get_param('user_password_strength.is_lower')
        config_special_symbol = get_param('user_password_strength'
                                          '.is_special_symbol')

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if qcontext and request.httprequest.method == 'POST':
            if config_strength and (len(str(values.get('password'))) < 8):
                qcontext['error'] = _(
                    "*****The Password Should have 8 characters." "")
            else:
                current_password = str(values.get('password'))
                if config_digit and (re.search('[0-9]', current_password)
                                     is None):
                    qcontext['error'] = _(
                        "*****The Password Should have at least one number.")
                if config_upper and (re.search('[A-Z]', current_password)
                                     is None):
                    qcontext['error'] = _(
                        "*****The Password Should have at least "
                        "one uppercase character.")
                if config_lower and (re.search("[a-z]", current_password)
                                     is None):
                    qcontext['error'] = _(
                        "*****The Password Should have at least one "
                        "lowercase character.")
                if config_special_symbol and \
                        (re.search("[~!@#$%^&*]", current_password) is None):
                    qcontext['error'] = _(
                        "*****The Password Should have at least "
                        "one special symbol.")
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                User = request.env['res.users']
                user_sudo = User.sudo().search(
                    User._get_login_domain(qcontext.get('login')),
                    order=User._get_login_order(), limit=1
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
                        "Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/web/config_params', type='json', auth="public")
    def website_get_config_value(self):
        """returning the values from config settings to js"""
        get_param = request.env['ir.config_parameter'].sudo().get_param
        return {
            'config_strength': get_param('user_password_strength.is_strength'),
            'config_digit': get_param('user_password_strength.is_digit'),
            'config_upper': get_param('user_password_strength.is_upper'),
            'config_lower': get_param('user_password_strength.is_lower'),
            'config_special_symbol': get_param('user_password_strength'
                                               '.is_special_symbol')
        }

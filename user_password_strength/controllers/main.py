# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Farha V C (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http, _
from odoo.addons.web.controllers.home import Home, LOGIN_SUCCESSFUL_PARAMS
from odoo.exceptions import UserError
from odoo.http import request
import re
LOGIN_SUCCESSFUL_PARAMS.add('account_created')


class PasswordSecurity(Home):
    """overriding the website signup controller"""
    def _prepare_signup_values(self, qcontext):
        """getting the values from config settings"""
        values = {key: qcontext.get(key) for key in ('login', 'name',
                                                     'password')}
        get_param = request.env['ir.config_parameter'].sudo().get_param
        config_strength = get_param('user_password_strength.is_strength')
        config_digit = get_param('user_password_strength.is_digit')
        config_upper = get_param('user_password_strength.is_upper')
        config_lower = get_param('user_password_strength.is_lower')
        config_special_symbol = get_param('user_password_strength'
                                          '.is_special_symbol')

        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        if values.get('password'):
            current_password = str(values.get('password'))
            if config_strength and (len(current_password) < 8):
                raise UserError(_("*****The Password Should have 8 characters."
                                  ""))
            else:
                if config_digit and (re.search('[0-9]', current_password)
                                     is None):
                    raise UserError(_(
                        "*****The Password Should have at least one number."))
                if config_upper and (re.search('[A-Z]', current_password)
                                     is None):
                    raise UserError(_(
                        "*****The Password Should have at least "
                        "one uppercase character."))
                if config_lower and (re.search("[a-z]", current_password)
                                     is None):
                    raise UserError(_(
                        "*****The Password Should have at least one "
                        "lowercase character."))
                if config_special_symbol and \
                        (re.search("[~!@#$%^&*]", current_password) is None):
                    raise UserError(_(
                        "*****The Password Should have at least "
                        "one special symbol."))
        return super()._prepare_signup_values(qcontext)

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

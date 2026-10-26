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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import http
from odoo.http import request
from odoo.tools import config
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.database import Database
from .utils import (
    check_reset_password_enabled, is_throttled, register_failure,
    reset_failures)

FORGOT_PASSWORD_TEMPLATE = 'password_reset_manager.forgot_password'


class DatabaseInherit(Database):
    """Adds the password reset using the master password."""

    @http.route('/web/reset_by_master_pass/submit', type='http',
                methods=['POST'], auth='public', website=True)
    def change_password_by_master(self, **kw):
        """Change a user's password using the master password.

        :param kw: Keyword arguments received from the request.
        :return: A redirect to the login page on success, otherwise the form
         with an error message.
        """
        check_reset_password_enabled(AuthSignupHome())
        user_name = (kw.get('user_name') or '').strip()
        master_password = kw.get('master_password') or ''
        new_password = kw.get('new_password') or ''
        confirm_password = kw.get('confirm_new_password') or ''
        values = {'username': user_name}

        def _error(message):
            values['error'] = message
            return request.render(FORGOT_PASSWORD_TEMPLATE, values)

        if not (user_name and master_password and new_password
                and confirm_password):
            return _error(request.env._("Please fill in all the fields."))
        if new_password != confirm_password:
            return _error(request.env._("The passwords do not match."))
        if is_throttled('master_password'):
            return _error(request.env._("Too many failed attempts. Please try again "
                            "later."))
        if not config.verify_admin_password(master_password):
            register_failure('master_password')
            return _error(request.env._("The master password is incorrect."))
        reset_failures('master_password')
        user = request.env['res.users'].sudo().search(
            [('login', '=', user_name)], limit=1)
        if not user:
            return _error(request.env._("The user name is not valid."))
        user.write({'password': new_password})
        return request.redirect(
            '/web/login?message=%s' % request.env._("Password changed."))

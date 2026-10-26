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
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.http.session import authenticate as session_authenticate
from odoo.http.session import logout as session_logout
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from .utils import (
    check_reset_password_enabled, is_throttled, register_failure,
    reset_failures)

CHANGE_PASSWORD_TEMPLATE = 'password_reset_manager.reset_password_direct'


class AuthSignupHomeInherit(AuthSignupHome):
    """Adds the "Forgot Password" and "Change Password" pages."""

    @http.route('/web/forgot_password', type='http', auth='public',
                website=True, sitemap=False)
    def forgot_password(self):
        """Render the page used to reset a password with the master password.

        :return: A response containing the "forgot_password" template.
        """
        qcontext = check_reset_password_enabled(self)
        return request.render('password_reset_manager.forgot_password',
                              qcontext)

    @http.route('/web/reset_password/direct', type='http', auth='public',
                website=True, sitemap=False)
    def web_auth_reset_password_direct(self):
        """Render the page used to change a password with the old one.

        :return: A response containing the "reset_password_direct" template.
        """
        qcontext = check_reset_password_enabled(self)
        return request.render(CHANGE_PASSWORD_TEMPLATE, qcontext)

    @http.route('/web/reset_password/submit', type='http',
                methods=['POST'], auth='public', website=True)
    def change_password(self, **kw):
        """Change the password of a user, after checking the old password.

        :param kw: Keyword arguments received from the request.
        :return: A redirect to the login page on success, otherwise the form
         with an error message.
        """
        check_reset_password_enabled(self)
        user_name = (kw.get('user_name') or '').strip()
        old_password = kw.get('old_password') or ''
        new_password = kw.get('new_password') or ''
        confirm_password = kw.get('confirm_new_password') or ''
        values = {'username': user_name}

        def _error(message):
            values['error'] = message
            return request.render(CHANGE_PASSWORD_TEMPLATE, values)

        if not (user_name and old_password and new_password
                and confirm_password):
            return _error(request.env._("Please fill in all the fields."))
        if new_password != confirm_password:
            return _error(request.env._("The passwords do not match."))
        if is_throttled('change_password'):
            return _error(request.env._("Too many failed attempts. Please try again "
                            "later."))
        try:
            credential = {'login': user_name, 'password': old_password,
                          'type': 'password'}
            auth_info = session_authenticate(
                request.session, request.env, credential)
        except AccessDenied:
            register_failure('change_password')
            return _error(request.env._("Login or password is incorrect."))
        reset_failures('change_password')
        user = request.env['res.users'].browse(auth_info['uid'])
        if user.has_group('base.group_public'):
            return _error(request.env._("Public users can't change their password."))
        user.sudo().write({'password': new_password})
        session_logout(request.session, keep_db=True)
        return request.redirect(
            '/web/login?message=%s' % request.env._("Password changed."))

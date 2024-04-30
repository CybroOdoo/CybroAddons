# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
import odoo
from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class AuthSignupHomeInherit(AuthSignupHome):
    @http.route('/web/forgot_password', type='http', auth='public',
                website=True, sitemap=False, csrf=False)
    def forgot_password(self):
        """
        Handle the "Forgot Password" functionality.

        :return: A response containing the "forgot_password" template with the
         context data.
        """
        qcontext = self.get_auth_signup_qcontext()
        response = request.render('password_reset_manager.forgot_password',
                                  qcontext)
        return response

    @http.route('/web/reset_password/direct', type='http', auth='public',
                website=True, sitemap=False, csrf=False, )
    def web_auth_reset_password_direct(self):
        """
        Handle the direct reset password functionality for web authentication.

        :return: A response containing the "reset_password_direct" template
         with the context data.
        """
        qcontext = self.get_auth_signup_qcontext()
        response = request.render(
            'password_reset_manager.reset_password_direct', qcontext)
        return response

    @http.route('/web/reset_password/submit', type='http',
                methods=['POST'], auth="public", website=True, csrf=False)
    def change_password(self, **kw):
        """
        Handle the password change functionality for a user.

        :param kw: Keyword arguments received from the request.

        :return: A redirect to the login page with a success message or an
         error message.
        """
        values = {}

        # Check if the new password and confirm new password match.
        if kw['confirm_new_password'] == kw['new_password']:
            try:
                # Authenticate the user session with the provided old password
                uid = request.session.authenticate(request.session.db,
                                                   kw['user_name'],
                                                   kw['old_password'])
                user = request.env['res.users'].search([('id', '=', uid)])
                is_user_public = request.env.user.has_group(
                    'base.group_public')
                if not is_user_public:
                    # Update the user's password with the new password.
                    user.sudo().write({
                        'password':  kw['confirm_new_password']
                    })

                    # Redirect to the login page with a success message.
                    return request.redirect('/web/login?message=%s'
                                            % _('Password Changed'))
                else:
                    values['error'] = _(
                        "Public users can't change their password")
                    return request.render(
                        'password_reset_manager.reset_password_direct', values)
            except odoo.exceptions.AccessDenied as e:
                values['error'] = _("Login or Password Is Incorrect")
                return request.render(
                    'password_reset_manager.reset_password_direct', values)
        else:
            values['error'] = _("Password Not Match")
            return request.render(
                'password_reset_manager.reset_password_direct', values)

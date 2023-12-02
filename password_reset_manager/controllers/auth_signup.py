# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
################################################################################
from werkzeug.utils import redirect
import odoo
from odoo import http, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.main import Database


class DataBase(Database):
    """Inherits 'Database' to add functionalities of resetting password."""

    @http.route(route='/web/reset_by_master_pass/submit', type='http',
                methods=['POST'], auth="public", website=True, csrf=False)
    def change_password_by_master(self, *args, **kw):
        """This route is called when while confirm the "Reset password" form
            and change the password using the master password."""
        values = {}
        if kw['confirm_new_password'] == kw['new_password']:
            if odoo.tools.config.verify_admin_password(kw['master_password']):
                user_valid = (request.env['res.users'].sudo().
                              search([('login', '=', kw['user_name'])]))
                if user_valid:
                    query = (f"update res_users set password='%s' where "
                             "login='%s'") % (
                                kw['confirm_new_password'], kw['user_name'])
                    request.cr.execute(query)
                    return redirect(f'/web/login?message=%s' %
                                    _('Password Changed'))
                else:
                    values['error'] = _("User Name Is Not Valid")
                    return request.render('password_reset_manager.'
                                          'forgot_password', values)
            else:
                values['error'] = _("Master Password Is Incorrect")
                return request.render('password_reset_manager.forgot_password',
                                      values)
        else:
            values['error'] = _("Password Not Matched")
            return request.render('password_reset_manager.forgot_password',
                                  values)


class AuthSignupHome(AuthSignupHome):
    """Inherits 'AuthSignupHome' to add functions while clicking
       'Forgot Password'"""

    @http.route(route='/web/forgot_password', type='http', auth='public',
                website=True, sitemap=False, csrf=False)
    def forgot_password(self, *args, **kw):
        """Route which called while clicking "Forgot Password" link from
            login page."""
        return request.render('password_reset_manager.forgot_password',
                              self.get_auth_signup_qcontext())

    @http.route(route='/web/reset_password/direct', type='http', auth='public',
                website=True, sitemap=False, csrf=False)
    def web_auth_reset_password_direct(self, *args, **kw):
        """Route which called while clicking "Change Password" link from
            login page."""
        return request.render('password_reset_manager.reset_password_direct'
                              , self.get_auth_signup_qcontext())

    @http.route(route='/web/reset_password/submit', type='http',
                methods=['POST'], auth="public", website=True, csrf=False)
    def change_password(self, *args, **kw):
        """This route is called when while confirm the "Change Password Form"
            section and change password using master password."""
        values = {}
        if kw['confirm_new_password'] == kw['new_password']:
            try:
                uid = request.session.authenticate(request.session.db,
                                                   kw['user_name'],
                                                   kw['old_password'])
                user = request.env['res.users'].search([('id', '=', uid)])
                user.password = kw['confirm_new_password']
                return redirect('/web/login?message=%s' %_('Password Changed'))
            except odoo.exceptions.AccessDenied:
                values['error'] = _("Login or Password Is Incorrect")
                return request.render('password_reset_manager.'
                                      'reset_password_direct', values)
        else:
            values['error'] = _("Password Not Match")
            return request.render('password_reset_manager.reset_password_direct'
                                  , values)

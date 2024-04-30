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
from odoo.http import request
from odoo.addons.web.controllers.database import Database


class DatabaseInherit(Database):
    @http.route('/web/reset_by_master_pass/submit', type='http',
                methods=['POST'], auth="public", website=True, csrf=False)
    def change_password_by_master(self, **kw):
        """
        Endpoint to change a user's password by a master password.

        :param kw: Keyword arguments received from the request.

        :return: A redirect to the login page with a success message or an
         error message.
        """
        values = {}

        # Check if the new password and confirm new password match.
        if kw['confirm_new_password'] == kw['new_password']:
            # Verify the master password using Odoo's config.
            if odoo.tools.config.verify_admin_password(kw['master_password']):
                # Search for a user with the provided user_name.
                user_valid = request.env['res.users'].sudo().search([
                    ('login', '=', kw['user_name'])])
                if user_valid:
                    # Update the user's password with the new password.
                    user_valid.sudo().write({
                        'password': kw['confirm_new_password']
                    })
                    # Redirect to the login page with a success message.
                    return request.redirect('/web/login?message=%s'
                                            % _('Password Changed'))
                else:
                    values['error'] = _("User Name Is Not Valid")
                    return request.render(
                        'password_reset_manager.forgot_password', values)
            else:
                values['error'] = _("Master Password Is Incorrect")
                return request.render('password_reset_manager.forgot_password',
                                      values)

        else:
            values['error'] = _("Password Not Matched")
            return request.render('password_reset_manager.forgot_password',
                                  values)

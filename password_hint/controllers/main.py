# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arjun P Manoj(odoo@cybrosys.com)
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
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo import http


class PasswordHint(AuthSignupHome):
    """
        A class that handles password hints during user signup and retrieval.

        Inherits from AuthSignupHome, a class that provides authentication and
        signup functionality for web users in the Odoo web application framework.
    """

    def web_auth_signup(self, *args, **kw):
        """
               Handle user signup and set password hint if provided.

               Args:
                   *args: Variable-length argument list.
                   **kw: Keyword arguments.

               Returns:
                   Result of calling the parent method.

        """
        res = super(PasswordHint, self).web_auth_signup()
        if kw.get('hint'):
            user = request.env['res.users'].sudo().search(
                [('login', '=', kw['login'])])
            user.password_hint = kw.get('hint')
        return res

    @http.route('/website/password/hint', type='json', auth='public',
                website=True)
    def button_password_hint(self, params):
        """
              Retrieve password hint for a given user login.

              Args:
                  params: JSON object containing user login.

              Returns:
                  JSON response containing password hint.

        """
        user = request.env['res.users'].sudo().search(
            [('login', '=', params)])
        value = user.password_hint
        return value

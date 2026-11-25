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
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.home import SIGN_UP_REQUEST_PARAMS
from odoo.http import route, request

# Add 'hint' to allowed signup request parameters so it is preserved in qcontext
SIGN_UP_REQUEST_PARAMS.add('hint')


class PasswordHint(AuthSignupHome):
    """
        A class that handles password hints during user signup and retrieval.
        Inherits from AuthSignupHome, a class that provides authentication and
        signup functionality for web users in the Odoo web application
        framework.
    """

    def _prepare_signup_values(self, qcontext, **kwargs):
        """Prepare values for creating a user on signup, including password hint."""
        values = super()._prepare_signup_values(qcontext, **kwargs)
        hint = qcontext.get('hint')
        if not hint:
            try:
                hint = request.params.get('hint')
            except Exception:
                hint = None
        if hint:
            values['password_hint'] = hint
        return values

    @route('/website/password/hint', type='jsonrpc', auth='public',
           website=True)
    def button_password_hint(self, login=None, **kwargs):
        """Retrieve password hint for a given portal user login.
            Args:
                login: User login (email).
                **kwargs: Additional keyword arguments.
            Returns:
                JSON response containing password hint or False.
        """
        if not login:
            return False
        User = request.env['res.users']
        user = User.sudo().search(User._get_login_domain(login), limit=1)
        # Limit hint retrieval to portal/share users to prevent disclosing internal/admin hints
        if not user or not user.share:
            return False
        return user.password_hint or False

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
import odoo
from odoo.http.session import Session, finalize
from odoo.tools.misc import get_lang


def authenticate_without_password(self, dbname, login, env):
    """Function for login without password in Odoo 20"""
    if not all([dbname, login]):
        return None
    # Get user
    user = env['res.users'].sudo().search([('login', '=', login)], limit=1)
    if not user:
        return None
    # Store session data
    self.uid = None
    self['pre_login'] = login
    self['pre_uid'] = user.id
    # Check 2FA requirement and authenticate if not required
    if not user._mfa_url():
        finalize(self, env)
    # Update request environment if applicable
    request = getattr(odoo.http, 'request', None)
    if request and getattr(request, 'session', None) is self and getattr(request, 'db', None) == dbname:
        request.env = env(user=self.uid, context=self.context)
        request.update_context(lang=get_lang(request.env(user=user.id)).code)
    return user.id


Session.authenticate_without_password = authenticate_without_password


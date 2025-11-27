# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import odoo
from odoo.http import request, Session
from odoo.modules.registry import Registry


def authenticate_without_password(self, dbname, login, env):
    """Function for login without password"""
    # validation
    if not all([dbname, login]):
        return None
    # Get user
    user_domain = [("login", "=", login)]
    user = env['res.users'].search(user_domain, limit=1)
    if not user:
        return None
    # Store session data
    self.update({
        'uid': None,
        'pre_login': login,
        'pre_uid': user.id
    })
    # Check 2FA requirement and authenticate if not required
    if not user._mfa_url():
        with Registry(dbname).cursor() as cr:
            user_env = odoo.api.Environment(cr, user.id, {})
            self.finalize(user_env)
    # Update request environment if applicable
    request = odoo.http.request
    if request and getattr(request, 'session', None) is self and getattr(request, 'db', None) == dbname:
        request.env = odoo.api.Environment(request.env.cr, self.uid, self.context)
        request.update_context(**self.context)
    return user.id

Session.authenticate_without_password = authenticate_without_password

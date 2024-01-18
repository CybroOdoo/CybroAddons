# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sabeel B (odoo@cybrosys.com)
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
    registry = Registry(dbname)
    pre_uid = env['res.users'].search([("login", '=', login)]).id
    self.uid = None
    self.pre_login = login
    self.pre_uid = pre_uid
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, pre_uid, {})
        # If 2FA is disabled we finalize immediately
        user = env['res.users'].browse(pre_uid)
        if not user._mfa_url():
            self.finalize(env)
    if request and request.session is self and request.db == dbname:
        # Like update_env(user=request.session.uid) but works when uid is None
        request.env = odoo.api.Environment(request.env.cr, self.uid,
                                           self.context)
        request.update_context(**self.context)
    return pre_uid


Session.authenticate_without_password = authenticate_without_password

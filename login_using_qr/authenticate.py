# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author: Anjhana A K (odoo@cybrosys.com)
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
from odoo.http import request
from odoo.modules.registry import Registry
from odoo.http import Session


def authenticate_without_passwd(self, dbname, login):
    """This function creates a authentication methode without password"""
    registry = Registry(dbname)
    pre_uid = request.env['res.users'].sudo().search([('login', '=', login)]).id
    self.uid = None
    self.pre_login = login
    self.pre_uid = pre_uid
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, pre_uid, {})
        user = env['res.users'].browse(pre_uid)
        if not user._mfa_url():
            self.finalize(env)
    if request and request.session is self and request.db == dbname:
        request.env = odoo.api.Environment(request.env.cr, self.uid,
                                           self.context)
        request.update_context(**self.context)
    return pre_uid
Session.authenticate_without_passwd = authenticate_without_passwd

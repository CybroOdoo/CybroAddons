# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import logging
_logger = logging.getLogger(__name__)


def authenticate_without_passwd(self, dbname, login):
    """This function creates a authentication method without password"""
    registry = Registry(dbname)
    # Find user
    user = request.env['res.users'].sudo().search([('login', '=', login)])
    if not user:
        raise Exception(f"User {login} not found")
    pre_uid = user.id
    # Set up session data as expected by finalize()
    # The finalize method expects certain keys to be present in the session
    self.db = dbname
    self.login = login
    self.uid = pre_uid
    # Set the pre_login and pre_uid in session data (not as attributes)
    self['pre_login'] = login
    self['pre_uid'] = pre_uid
    self['login'] = login
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, pre_uid, {})
        user_env = env['res.users'].browse(pre_uid)
        # Check MFA
        if not user_env._mfa_url():
            self.finalize(env)
        else:
            _logger.info("MFA detected - QR auth may need additional handling")
    # Update request environment if this is the current session
    if request and request.session is self and request.db == dbname:
        request.env = odoo.api.Environment(request.env.cr, self.uid, self.context)
        request.update_context(**self.context)
    return pre_uid
Session.authenticate_without_passwd = authenticate_without_passwd

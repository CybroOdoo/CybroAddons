# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    """Extend res.users to add login restriction functionality."""
    _inherit = 'res.users'

    login_restriction_id = fields.One2many(
        'login.restriction.config',
        'user_id',
        string='Login Restrictions',
        help='Working hours login restrictions for this user'
    )

    def check_login_restrictions(self):
        """
        Check if the user is allowed to login at the current time.
        
        Raises:
            AccessDenied: If login is restricted and user is not authorized
        """
        if not self:
            return True
        self = self.sudo()
        # Since self can be a recordset, we should ensure we are checking for a single user
        # In context of login/authenticate, it should always be a singleton if not empty
        self.ensure_one()
        restriction = self.env['login.restriction.config'].sudo().search([
            ('user_id', '=', self.id)
        ], limit=1)
        if not restriction or not restriction.is_restricted:
            return True
        # Check if user is admin and allowed to bypass
        if restriction.allow_admin_bypass and self.has_group('base.group_system'):
            return True
        # Check if current time is within working hours
        if not restriction.is_within_working_hours():
            raise AccessDenied(restriction.error_message)
        return True

    @classmethod
    def _login(cls, db, credential, user_agent_env=None):
        """Override _login to enforce login restrictions."""
        # Correct signature for Odoo 18+
        auth_info = super()._login(db, credential, user_agent_env=user_agent_env)
        
        uid = auth_info.get('uid') if isinstance(auth_info, dict) else auth_info
        
        if uid:
            from odoo import api, SUPERUSER_ID
            from odoo.modules.registry import Registry
            registry = Registry(db)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                user = env['res.users'].browse(uid)
                if user.exists():
                    try:
                        user.check_login_restrictions()
                    except AccessDenied as e:
                        # You might want to log this or handle session-specific data here
                        raise e
        return auth_info


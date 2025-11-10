# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
from odoo import _, api, Command, fields, models


class ResUsers(models.Model):
    """Extends res.users to integrate access roles and role-based permissions."""
    _inherit = 'res.users'

    access_role_id = fields.Many2one('access.role', string='Access Role',
                                     help='Select the role of the user')

    @api.onchange('access_role_id')
    def _onchange_access_role_id(self):
        """Warn users to save before assigning a role and update user-role relationships."""
        if not self._origin.id and self.access_role_id:  # Record is new (not saved)
            self.access_role_id = False
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _("Please save the user before assigning an Access Role."),
                }
            }
        if not self.user_id:
            if self._origin.access_role_id:
                self._origin.access_role_id.write(
                    {'user_ids': [(fields.Command.unlink(self._origin.id))]})
            # Assign user to the new role
            if self.access_role_id:
                self.access_role_id.write(
                    {'user_ids': [(fields.Command.link(self._origin.id))]})
        else:
            # Remove user from the previous role
            if self._origin.access_role_id:
                self._origin.access_role_id.write(
                    {'user_ids': [(fields.Command.unlink(self.user_id.id))]})
            # Assign user to the new role
            if self.access_role_id:
                self.access_role_id.write(
                    {'user_ids': [(fields.Command.link(self.user_id.id))]})

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to assign groups based on the selected access role and creation of new users."""
        users = super(ResUsers, self).create(vals_list)
        for user in users:
            if user.access_role_id:
                user.write({
                    'groups_ids': [Command.set(user.access_role_id.groups_id.ids)]
                })
        return users

    def write(self, vals):
        """Override write to manage role-based group assignment"""
        groups_to_remove = None
        # Handle role removal
        if 'access_role_id' in vals and not vals['access_role_id']:
            if self.access_role_id:
                groups_to_remove = self.access_role_id.groups_ids
        result = super(ResUsers, self).write(vals)
        if 'access_role_id' in vals:
            if vals['access_role_id']:
                new_role = self.env['access.role'].browse(vals['access_role_id'])
                self.write({
                    'groups_id': [Command.set(new_role.groups_ids.ids)]
                })
            elif groups_to_remove:
                groups_list = groups_to_remove.ids
                if 1 in groups_list:
                    groups_list.remove(1)
                self.write({
                    'groups_id': [Command.unlink(gid) for gid in groups_list]
                })
        return result

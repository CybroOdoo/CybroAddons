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
from odoo import api, fields, models
from odoo.fields import Command


class ResUsers(models.Model):
    """Extends res.users to integrate access roles and role-based permissions."""
    _inherit = 'res.users'

    access_role_id = fields.Many2one('access.role', string='Access Role',
                                     help='Select the role of the user')

    @api.onchange('access_role_id')
    def _onchange_access_role_id(self):
        """Warn users to save before assigning a role."""
        if not self._origin.id and self.access_role_id:
            self.access_role_id = False
            return {
                'warning': {
                    'title': self.env._("Warning"),
                    'message': self.env._("Please save the user before assigning an Access Role."),
                }
            }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to assign groups based on the selected access role."""
        users = super(ResUsers, self).create(vals_list)
        for user in users:
            if user.access_role_id:
                user.write({
                    'group_ids': [Command.set(user.access_role_id.groups_ids.ids)]
                })
                if user.id not in user.access_role_id.user_ids.ids:
                    user.access_role_id.write({'user_ids': [Command.link(user.id)]})
        if any(u.access_role_id for u in users):
            self.env.invalidate_all()
            self.env.transaction.invalidate_ormcache()
            self.env.transaction.invalidate_ormcache('templates')
        return users

    def write(self, vals):
        """Override write to manage role-based group assignment"""
        groups_to_remove_per_user = {}
        old_roles_per_user = {}
        if 'access_role_id' in vals:
            for user in self:
                if user.access_role_id:
                    groups_to_remove_per_user[user.id] = user.access_role_id.groups_ids
                    old_roles_per_user[user.id] = user.access_role_id
        result = super(ResUsers, self).write(vals)
        if 'access_role_id' in vals:
            if vals['access_role_id']:
                new_role = self.env['access.role'].browse(vals['access_role_id'])
                for user in self:
                    user.write({
                        'group_ids': [Command.set(new_role.groups_ids.ids)]
                    })
                    old_role = old_roles_per_user.get(user.id)
                    if old_role and old_role != new_role:
                        old_role.write({'user_ids': [Command.unlink(user.id)]})
                    if user.id not in new_role.user_ids.ids:
                        new_role.write({'user_ids': [Command.link(user.id)]})
            elif groups_to_remove_per_user:
                for user in self:
                    groups_to_remove = groups_to_remove_per_user.get(user.id)
                    old_role = old_roles_per_user.get(user.id)
                    if old_role:
                        old_role.write({'user_ids': [Command.unlink(user.id)]})
                    if groups_to_remove:
                        groups_list = list(groups_to_remove.ids)
                        if 1 in groups_list:
                            groups_list.remove(1)
                        user.write({
                            'group_ids': [Command.unlink(gid) for gid in groups_list]
                        })
            self.env.invalidate_all()
            self.env.transaction.invalidate_ormcache()
            self.env.transaction.invalidate_ormcache('templates')
        return result

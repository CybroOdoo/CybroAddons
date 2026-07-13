# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command, api, fields, models


class ResUsers(models.Model):
    """Manage per-user hidden menu items."""
    _inherit = 'res.users'

    hide_menu_ids = fields.Many2many(
        comodel_name='ir.ui.menu',
        string="Hidden Menu",
        help="Menu items that will be hidden from this user.")
    is_show_specific_menu = fields.Boolean(
        string="Is Show Specific Menu",
        compute='_compute_is_show_specific_menu',
        help="Technical field: True when the user is not an internal user, "
             "used to hide the specific-menu configuration page.")

    @api.depends('group_ids')
    def _compute_is_show_specific_menu(self):
        """Only internal users may be assigned hidden menus."""
        for user in self:
            user.is_show_specific_menu = not user.has_group('base.group_user')

    def _sync_restricted_menus(self, old_hide_menu_map):
        """Mirror ``hide_menu_ids`` onto each menu's ``restrict_user_ids``."""
        for user in self:
            old_menus = old_hide_menu_map.get(user.id, self.env['ir.ui.menu'])
            added = user.hide_menu_ids - old_menus
            removed = old_menus - user.hide_menu_ids
            if added:
                added.sudo().write(
                    {'restrict_user_ids': [Command.link(user.id)]})
            if removed:
                removed.sudo().write(
                    {'restrict_user_ids': [Command.unlink(user.id)]})

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._sync_restricted_menus(
            {user.id: self.env['ir.ui.menu'] for user in users})
        return users

    def write(self, vals):
        relevant = 'hide_menu_ids' in vals or 'group_ids' in vals
        old_hide_menu_map = (
            {user.id: user.hide_menu_ids for user in self} if relevant else {})
        res = super().write(vals)
        if relevant:
            # Non-internal users must not keep hidden menus.
            to_clear = self.filtered(
                lambda user: user.hide_menu_ids
                and not user.has_group('base.group_user'))
            if to_clear:
                super(ResUsers, to_clear).write(
                    {'hide_menu_ids': [Command.clear()]})
            self._sync_restricted_menus(old_hide_menu_map)
        return res

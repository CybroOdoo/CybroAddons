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
from odoo import Command, fields, models


class IrUiMenu(models.Model):
    """Restrict menu items from being displayed to specific users."""
    _inherit = 'ir.ui.menu'

    restrict_user_ids = fields.Many2many(
        comodel_name='res.users',
        string="Restricted Users",
        help="Users restricted from accessing this menu.")
    restrict_group_ids = fields.Many2many(
        comodel_name='res.groups',
        relation='hide_menu_restrict_group_rel',
        column1='menu_id',
        column2='group_id',
        string="Restricted Groups",
        help="Users belonging to these groups are restricted from "
             "accessing this menu.")

    def _filter_visible_menus(self):
        """Hide menus restricted for the current user or their groups.

        System administrators are never restricted and always see the
        full menu hierarchy.
        """
        menus = super()._filter_visible_menus()
        user = self.env.user
        if user.has_group('base.group_system'):
            return menus
        user_group_ids = set(user._get_group_ids())
        return menus.filtered(
            lambda menu: user not in menu.restrict_user_ids
            and not user_group_ids.intersection(menu.restrict_group_ids.ids))

    def action_restrict_submenus(self):
        """Copy this menu's restrictions onto all of its descendant menus."""
        self.ensure_one()
        descendants = self.search(
            [('id', 'child_of', self.id), ('id', '!=', self.id)])
        if descendants:
            descendants.write({
                'restrict_user_ids': [
                    Command.link(user_id)
                    for user_id in self.restrict_user_ids.ids],
                'restrict_group_ids': [
                    Command.link(group_id)
                    for group_id in self.restrict_group_ids.ids],
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': False,
                'message': self.env._(
                    "Restrictions applied to %s sub-menu(s).",
                    len(descendants)),
            },
        }

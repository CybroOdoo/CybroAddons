# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models, api


class ResUsers(models.Model):
    """
    Model to handle hiding specific menu items for certain users.
    """
    _inherit = 'res.users'

    def write(self, vals):
        # Store old hide_menu_ids per record
        old_hide_menu_map = {record.id: record.hide_menu_ids for record in self}
        res = super(ResUsers, self).write(vals)
        for record in self:
            old_hide_menu_ids = old_hide_menu_map.get(record.id,
                                                     self.env['ir.ui.menu'])

            # Add new restrictions
            for menu in record.hide_menu_ids:
                menu.sudo().write({'restrict_user_ids': [(4, record.id)]})

            # Remove old ones that are no longer selected
            removed_menus = old_hide_menu_ids - record.hide_menu_ids
            for menu in removed_menus:
                menu.sudo().write({'restrict_user_ids': [(3, record.id)]})
        return res

    def _get_is_admin(self):
        """
        Compute method to check if the user is an admin.
        The Hide specific menu tab will be hidden for the Admin user form.
        """
        for rec in self:
            rec.is_admin = False
            if rec.id == self.env.ref('base.user_admin').id:
                rec.is_admin = True

    hide_menu_ids = fields.Many2many(
        'ir.ui.menu', string="Hidden Menu",
        store=True, help='Select menu items that need to '
                         'be hidden to this user.')
    is_admin = fields.Boolean(compute='_get_is_admin', string="Is Admin",
                              help='Check if the user is an admin.')


class IrUiMenu(models.Model):
    """
    Model to restrict the menu for specific users.
    """
    _inherit = 'ir.ui.menu'

    restrict_user_ids = fields.Many2many(
        'res.users', string="Restricted Users",
        help='Users restricted from accessing this menu.')

    @api.returns('self')
    def _filter_visible_menus(self):
        """
        Override to filter out menus restricted for current user.
        Applies only to the current user context.
        """
        menus = super(IrUiMenu, self)._filter_visible_menus()

        # Allow system admin to see everything
        if self.env.user.has_group('base.group_system'):
            return menus

        return menus.filtered(
            lambda m: self.env.user not in m.restrict_user_ids)

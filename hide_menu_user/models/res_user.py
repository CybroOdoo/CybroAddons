# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class HideMenuUser(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        """Clear caches to ensure menu visibility updates"""
        self.clear_caches()
        return super(HideMenuUser, self).create(vals_list)

    def write(self, vals):
        """Update menu restrictions and clear caches"""
        res = super(HideMenuUser, self).write(vals)
        for record in self:
            if 'hide_menu_ids' in vals:
                for menu in record.hide_menu_ids:
                    menu.write({
                        'restrict_user_ids': [(4, record.id)]
                    })
                # Remove user from restrict_user_ids for menus no longer in hide_menu_ids
                menus_to_remove = self.env['ir.ui.menu'].search([
                    ('restrict_user_ids', 'in', [record.id]),
                    ('id', 'not in', record.hide_menu_ids.ids)
                ])
                for menu in menus_to_remove:
                    menu.write({
                        'restrict_user_ids': [(3, record.id)]
                    })
        self.clear_caches()
        return res

    @api.depends('groups_id')
    def _compute_is_admin(self):
        """Determine if user is admin to control menu hiding visibility"""
        for rec in self:
            rec.is_admin = rec.id == self.env.ref('base.user_admin').id or \
                           rec.has_group('base.group_system')

    hide_menu_ids = fields.Many2many(
        'ir.ui.menu',
        string="Hidden Menus",
        store=True,
        help='Select menu items to hide for this user'
    )
    is_admin = fields.Boolean(
        compute='_compute_is_admin',
        string="Is Admin",
        help="Indicates if user has admin privileges"
    )


class RestrictMenu(models.Model):
    _inherit = 'ir.ui.menu'

    restrict_user_ids = fields.Many2many(
        'res.users',
        string='Restricted Users',
        help='Users for whom this menu is hidden'
    )

    @api.model
    def _visible_menu_ids(self, debug=False):
        """Override to filter out menus restricted for current user"""
        menu_ids = super(RestrictMenu, self)._visible_menu_ids(debug=debug)

        # Admin users see all menus
        if self.env.user.has_group('base.group_system'):
            return menu_ids

        # Filter out menus where current user is in restrict_user_ids
        restricted_menus = self.search([
            ('id', 'in', list(menu_ids)),
            ('restrict_user_ids', 'in', [self.env.user.id])
        ])
        return set(menu_ids) - set(restricted_menus.ids)

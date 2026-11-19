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
from odoo import api, models


class IrUiMenu(models.Model):
    """Extend ir.ui.menu to apply role-based UI restrictions."""
    _inherit = 'ir.ui.menu'

    def _get_role_hidden_menu_ids(self):
        """Return the set of menu IDs hidden for the current user's access role."""
        role = self.env.user.access_role_id
        if not role:
            return set()
        role_managements = self.env['role.management'].sudo().search([
            ('role_ids', 'in', role.id)
        ])
        if role.role_management_id:
            role_managements |= role.role_management_id
        menu_records = role_managements.mapped('menu_ids')
        if not menu_records:
            return set()
        all_hidden_menus = self.sudo().search([('id', 'child_of', menu_records.ids)])
        return set(all_hidden_menus.ids)

    def _load_menus_blacklist(self):
        """Hook into Odoo 20 load_menus to exclude blacklisted menus."""
        blacklist = super()._load_menus_blacklist()
        hidden_ids = self._get_role_hidden_menu_ids()
        if hidden_ids:
            return list(set(blacklist) | hidden_ids)
        return blacklist

    @api.model
    def _visible_menu_ids(self, debug=False):
        """Override to dynamically hide menus based on role management."""
        visible_menu_ids = super()._visible_menu_ids(debug=debug)
        hidden_menu_ids = self._get_role_hidden_menu_ids()
        if hidden_menu_ids:
            return visible_menu_ids - hidden_menu_ids
        return visible_menu_ids

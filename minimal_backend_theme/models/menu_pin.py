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


class MinimalBackendThemeMenuPin(models.Model):
    """A menu a user pinned from the top bar search or the sidebar: listed
    first in the search and in the sidebar. Personal, kept on the server so
    pins follow the user across browsers and devices."""

    _name = 'minimal_backend_theme.menu_pin'
    _description = 'Backend Theme: pinned menu'
    _order = 'sequence, id'

    user_id = fields.Many2one(
        'res.users', required=True, index=True, ondelete='cascade',
        default=lambda self: self.env.user,
    )
    menu_id = fields.Many2one('ir.ui.menu', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)

    _user_menu_unique = models.Constraint(
        'UNIQUE(user_id, menu_id)',
        "A menu can only be pinned once by a user.",
    )

    @api.model
    def get_pinned_menu_ids(self):
        """The current user's pinned menus, in pin order, keeping only those
        they can still see (a menu's groups may have changed since)."""
        pins = self.search([('user_id', '=', self.env.uid)])
        # Menus are not filtered by groups when searched: ask for visibility.
        visible = set(pins.menu_id._filter_visible_menus().ids)
        return [menu_id for menu_id in pins.menu_id.ids if menu_id in visible]

    @api.model
    def toggle_pin(self, menu_id):
        """Pins the menu, or unpins it if already pinned; returns the pinned
        menu ids."""
        pin = self.search([('user_id', '=', self.env.uid), ('menu_id', '=', menu_id)])
        if pin:
            pin.unlink()
        elif self.env['ir.ui.menu'].browse(menu_id).exists()._filter_visible_menus():
            last = self.search([('user_id', '=', self.env.uid)], order='sequence desc, id desc', limit=1)
            self.create({'menu_id': menu_id, 'sequence': last.sequence + 1 if last else 10})
        return self.get_pinned_menu_ids()

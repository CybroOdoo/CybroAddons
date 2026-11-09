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
from odoo.exceptions import UserError


class HideMenuFavorite(models.Model):
    """A menu a user starred to reach it quickly from the navbar."""
    _name = 'hide.menu.favorite'
    _description = 'Favourite Menu'
    _order = 'sequence, id'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="User",
        required=True,
        index=True,
        default=lambda self: self.env.user,
        ondelete='cascade')
    menu_id = fields.Many2one(
        comodel_name='ir.ui.menu',
        string="Menu",
        required=True,
        ondelete='cascade')
    sequence = fields.Integer(string="Sequence", default=10)

    _user_menu_unique = models.Constraint(
        'UNIQUE(user_id, menu_id)',
        "This menu is already in the user's favourites.",
    )

    @api.model
    def get_starred_menu_ids(self):
        """Return the menus to show in the current user's favourites menu.

        :return: dict with ``personal`` (menus the user starred) and
            ``shared`` (team shortcuts of the user's menu profile) as lists
            of menu ids; only menus the user can currently see are returned.
        """
        Menu = self.env['ir.ui.menu']
        personal = self.search(
            [('user_id', '=', self.env.uid)]).menu_id._filter_visible_menus()
        profile = self.env['hide.menu.profile']._get_for_user(self.env.user)
        # Re-browse in the user's environment so visibility is checked with
        # the user's own access rights, not the sudo-ed profile's.
        shared = Menu.browse(profile.shortcut_menu_ids.ids)
        shared = (shared - personal)._filter_visible_menus()
        return {'personal': personal.ids, 'shared': shared.ids}

    @api.model
    def toggle_star(self, menu_id):
        """Star or un-star a menu for the current user.

        :param int menu_id: the ``ir.ui.menu`` to toggle
        :return: True if the menu is now a favourite, False otherwise
        """
        menu_id = int(menu_id)
        favorite = self.search(
            [('user_id', '=', self.env.uid), ('menu_id', '=', menu_id)])
        if favorite:
            favorite.unlink()
            return False
        menu = self.env['ir.ui.menu'].browse(menu_id).exists()
        if not menu or not menu.action or not menu._filter_visible_menus():
            raise UserError(self.env._(
                "This menu cannot be added to your favourites."))
        last = self.search([('user_id', '=', self.env.uid)],
                           order='sequence desc', limit=1)
        self.create({'menu_id': menu.id, 'sequence': last.sequence + 1})
        return True

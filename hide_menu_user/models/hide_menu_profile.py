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
from odoo import Command, api, fields, models


class HideMenuProfile(models.Model):
    """A shared menu layout for a set of users and/or groups.

    A profile defines the default order of the apps and a list of team
    shortcuts shown in the favourites menu. The first active profile (by
    sequence) that matches a user applies to that user.
    """
    _name = 'hide.menu.profile'
    _description = 'Menu Profile'
    _order = 'sequence, id'

    name = fields.Char(string="Name", required=True, translate=True)
    sequence = fields.Integer(
        string="Priority",
        default=10,
        help="When several profiles match a user, the first one applies.")
    active = fields.Boolean(string="Active", default=True)
    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='hide_menu_profile_user_rel',
        column1='profile_id',
        column2='user_id',
        string="Users",
        domain=[('share', '=', False)],
        help="Users this profile applies to.")
    group_ids = fields.Many2many(
        comodel_name='res.groups',
        relation='hide_menu_profile_group_rel',
        column1='profile_id',
        column2='group_id',
        string="Groups",
        help="Members of these groups get this profile. Leave both Users "
             "and Groups empty to apply the profile to everyone.")
    app_ids = fields.One2many(
        comodel_name='hide.menu.profile.app',
        inverse_name='profile_id',
        string="App Order",
        copy=True,
        help="Apps listed here are shown first, in this order. Apps that "
             "are not listed keep their standard order after them.")
    shortcut_menu_ids = fields.Many2many(
        comodel_name='ir.ui.menu',
        relation='hide_menu_profile_shortcut_rel',
        column1='profile_id',
        column2='menu_id',
        string="Team Shortcuts",
        domain=[('action', '!=', False)],
        help="Menus pinned in the favourites menu of every user of this "
             "profile. Users only see the shortcuts they are allowed to "
             "open.")
    app_count = fields.Integer(
        string="Ordered Apps", compute='_compute_counts')
    shortcut_count = fields.Integer(
        string="Shortcuts", compute='_compute_counts')

    @api.depends('app_ids', 'shortcut_menu_ids')
    def _compute_counts(self):
        for profile in self:
            profile.app_count = len(profile.app_ids)
            profile.shortcut_count = len(profile.shortcut_menu_ids)

    def action_add_missing_apps(self):
        """Append every top-level app not yet in the order, so the
        administrator only has to drag them into place."""
        self.ensure_one()
        known_menus = self.app_ids.menu_id
        apps = self.env['ir.ui.menu'].search(
            [('parent_id', '=', False), ('id', 'not in', known_menus.ids)])
        next_sequence = max(self.app_ids.mapped('sequence'), default=0) + 1
        self.write({'app_ids': [
            Command.create({'menu_id': app.id, 'sequence': next_sequence + index})
            for index, app in enumerate(apps)
        ]})

    def _matches_user(self, user, user_group_ids):
        """Return whether this profile applies to ``user``."""
        self.ensure_one()
        if not self.user_ids and not self.group_ids:
            return True
        return user in self.user_ids or bool(
            user_group_ids.intersection(self.group_ids.ids))

    @api.model
    def _get_for_user(self, user):
        """Return the profile that applies to ``user`` (possibly empty).

        The result is a sudo-ed record: callers must re-browse any menu
        they expose in the user's environment.
        """
        if user.share:
            return self.sudo().browse()
        user_group_ids = set(user._get_group_ids())
        for profile in self.sudo().search([]):
            if profile._matches_user(user, user_group_ids):
                return profile
        return self.sudo().browse()

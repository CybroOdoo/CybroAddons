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
from odoo import fields, models


class HideMenuProfileApp(models.Model):
    """Position of one app in the order defined by a menu profile."""
    _name = 'hide.menu.profile.app'
    _description = 'Menu Profile App Position'
    _order = 'sequence, id'

    profile_id = fields.Many2one(
        comodel_name='hide.menu.profile',
        string="Profile",
        required=True,
        index=True,
        ondelete='cascade')
    sequence = fields.Integer(string="Sequence", default=10)
    menu_id = fields.Many2one(
        comodel_name='ir.ui.menu',
        string="App",
        required=True,
        ondelete='cascade',
        domain=[('parent_id', '=', False)])

    _profile_menu_unique = models.Constraint(
        'UNIQUE(profile_id, menu_id)',
        "An app can only appear once in a profile.",
    )

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


class ResUsersSettings(models.Model):
    """Store the personal app order chosen by each user."""
    _inherit = 'res.users.settings'

    hide_menu_app_order = fields.Json(
        string="Personal App Order",
        readonly=True,
        help="Ids of the apps in the order chosen by the user. Empty means "
             "the order of the user's menu profile applies.")

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._hide_menu_reset_home_order(vals)
                               for vals in vals_list])

    def write(self, vals):
        return super().write(self._hide_menu_reset_home_order(vals))

    def _hide_menu_reset_home_order(self, vals):
        """Drop the Enterprise home screen order when the personal app order
        changes, so a single order applies everywhere."""
        if 'hide_menu_app_order' in vals and 'homemenu_config' in self._fields:
            return {**vals, 'homemenu_config': False}
        return vals

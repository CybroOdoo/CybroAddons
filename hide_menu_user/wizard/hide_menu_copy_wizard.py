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


class HideMenuCopyWizard(models.TransientModel):
    """Wizard to copy the hidden menus of one user onto other users."""
    _name = 'hide.menu.copy.wizard'
    _description = 'Copy Hidden Menus Between Users'

    source_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Copy From",
        required=True,
        help="User whose hidden menus will be copied.")
    target_user_ids = fields.Many2many(
        comodel_name='res.users',
        string="Apply To",
        required=True,
        help="Users that will also get the hidden menus of the source user.")

    def action_copy(self):
        """Add the source user's hidden menus to every target user.

        Existing restrictions on the target users are kept; the copied
        menus are merged in.
        """
        self.ensure_one()
        source_menu_ids = self.source_user_id.hide_menu_ids.ids
        for user in self.target_user_ids - self.source_user_id:
            user.write({
                'hide_menu_ids': [Command.link(menu_id)
                                  for menu_id in source_menu_ids],
            })
        return {'type': 'ir.actions.act_window_close'}

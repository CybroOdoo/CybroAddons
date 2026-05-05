# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class ResUsers(models.Model):
    """Add sessions and buttons in the user form view"""
    _inherit = 'res.users'

    pos_session_ids = fields.Many2many('pos.session',
                                        domain=[('state', '!=', 'closed')],
                                        string="Pos Session",
                                        help="POS sessions where button restrictions apply.")

    pos_button_ids = fields.Many2many('pos.button',
                                       string="Pos Buttons",
                                       help="POS buttons that should be restricted for the user.")

    def pos_button_visibility(self, hide_buttons):
        """This is used to return the restricted button name"""
        pos_buttons = self.env['pos.button'].browse(hide_buttons).mapped('name')
        return pos_buttons

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Load POS fields for the user.

        pos_session_ids → sessions where the user should have restrictions
        pos_button_ids → buttons that should be hidden for the user
        """

        result = super()._load_pos_data_fields(config_id)
        result += ['pos_button_ids']
        result += ['pos_session_ids']
        return result


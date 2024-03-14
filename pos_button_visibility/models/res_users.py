# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu kp (<https://www.cybrosys.com>)
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
from odoo import fields, models


class ResUsers(models.Model):
    """Add sessions and buttons in the usr form"""
    _inherit = 'res.users'

    user_session_ids = fields.Many2many('pos.session',
                                        domain=[('state', '!=', 'closed')],
                                        string="Pos Session",
                                        help="Session of pos")
    buttons_pos_ids = fields.Many2many('pos.buttons',
                                       string="Pos Buttons",
                                       help="pos buttons")

    def pos_button_visibility(self, hidebuttons):
        """This is used to return the restricted button name"""
        pos_buttons = self.env['pos.buttons'].browse(hidebuttons).mapped('name')
        return pos_buttons

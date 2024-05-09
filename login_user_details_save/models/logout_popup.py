# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class LogoutPopup(models.Model):
    """Model for checking if user wants to save his login details"""
    _name = "logout.popup"
    _description = "Logout Popup"

    name = fields.Char(string="Name", default="name",
                       help="This is the name field")
    save_details = fields.Boolean(default=False,
                                  string="Save Login Details ?",
                                  help="Boolean field to save login details if enabled")
    user_id = fields.Many2one('res.users', string='User',
                              help="ID of the user whose login details must be saved")

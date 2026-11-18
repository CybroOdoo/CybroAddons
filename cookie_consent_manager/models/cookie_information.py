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

OBJECT_COLOR = {
    "0": "#FFFFFF",  # No color (default to white)
    "1": "#FF0000",  # Red
    "2": "#FFA500",  # Orange
    "3": "#FFFF00",  # Yellow
    "4": "#ADD8E6",  # Light blue
    "5": "#800080",  # Purple
    "6": "#FA8072",  # Salmon pink
    "7": "#0000CD",  # Medium blue
    "8": "#00008B",  # Dark blue
    "9": "#FF00FF",  # Fuchsia
    "10": "#008000",  # Green
    "11": "#4B0082",  # Indigo
}


class CookieInformation(models.Model):
    """This class is used to store information about a cookie template."""
    _name = "cookie.information"
    _description = "Cookie Information"
    _rec_name = 'template_title'

    template_title = fields.Char(string="Template Name",
                                 help="Title of the cookie template")
    pop_up_text = fields.Char(string="Popup Text",
                              help="Cookie consent message to display")
    cookie_color = fields.Integer(string="Cookie Color",
                                  help="Change the background color of the cookie banner")
    is_change_pop_up_position = fields.Boolean(
        string="Change Popup Position",
        help="Enable to customize the popup position")
    is_change_pop_up_position_top = fields.Boolean(
        string="Move to Top",
        help="Change the popup position to top")
    is_change_pop_up_position_bottom = fields.Boolean(
        string="Move to Bottom",
        help="Change the popup position to bottom")
    pop_up_position_top = fields.Selection([
        ('top_left', 'Top Left'),
        ('top_right', 'Top Right'),
        ('top_center', 'Top Center'),
        ('full_top_container', 'Full Top Container'),
    ], string="Popup Position on Top",
       help="Select the popup position on top")
    pop_up_position_bottom = fields.Selection([
        ('bottom_left', 'Bottom Left'),
        ('bottom_right', 'Bottom Right'),
        ('bottom_center', 'Bottom Center'),
        ('full_bottom_container', 'Full Bottom Container'),
    ], string="Popup Position on Bottom",
       help="Select the popup position on bottom")
    accept_btn_txt = fields.Char(string="Accept Button Text",
                                 help="Label for the Accept button")
    reject_btn_txt = fields.Char(string="Reject Button Text",
                                 help="Label for the Reject button")
    cookie_policy_btn = fields.Char(string="Policy Button Text",
                                    help="Label for the Cookie Policy link button")

    @api.onchange('is_change_pop_up_position')
    def _onchange_is_change_pop_up_position(self):
        """Reset position selections when custom position is disabled."""
        if not self.is_change_pop_up_position:
            self.is_change_pop_up_position_top = False
            self.is_change_pop_up_position_bottom = False
            self.pop_up_position_top = False
            self.pop_up_position_bottom = False

    @api.onchange('is_change_pop_up_position_top')
    def _onchange_is_change_pop_up_position_top(self):
        """Ensure bottom position is cleared when top position is selected."""
        if self.is_change_pop_up_position_top:
            self.is_change_pop_up_position_bottom = False
            self.pop_up_position_bottom = False

    @api.onchange('is_change_pop_up_position_bottom')
    def _onchange_is_change_pop_up_position_bottom(self):
        """Ensure top position is cleared when bottom position is selected."""
        if self.is_change_pop_up_position_bottom:
            self.is_change_pop_up_position_top = False
            self.pop_up_position_top = False

    @api.model
    def _get_color(self, value):
        """Get the color code corresponding to the given value."""
        return OBJECT_COLOR.get(str(value), "#FFFFFF")

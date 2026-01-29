# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C)2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ayana KP @cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


OBJECT_COLOR = {
    "0": "#FFFFFF",  # No color (default to white)
    "1": "#FF0000",  # Red
    "2": "#FFA500",  # Orange
    "3": "#FFFF00",  # Yellow
    "4": "#ADD8E6",  # Light blue
    "5": "#800080",  # Dark purple
    "6": "#FA8072",  # Salmon pink
    "7": "#0000CD",  # Medium blue
    "8": "#00008B",  # Dark blue
    "9": "#FF00FF",  # Fuchsia
    "10": "#008000",  # Green
    "11": "#800080",  # Purple
}


class CookieInformation(models.Model):
    """This class is used to store information about a cookie template."""
    _name = "cookie.information"
    _description = "Cookie Information"
    _rec_name = 'template_title'

    template_title = fields.Char(string="Template Name",
                                 help="Title of the template")
    pop_up_text = fields.Char(string="Pop Up text", help="Cookie message")
    cookie_color = fields.Integer(string="Cookie Color",
                                  help="Change the color of cookie")
    is_change_pop_up_position = fields.Boolean(string="Change Pop up position",
                                               help="Change the pop up "
                                                    "position")
    is_change_pop_up_position_top = fields.Boolean(
        string="Move to Top", help="Change the pop up position to top")
    is_change_pop_up_position_bottom = fields.Boolean(
        string="Move to Bottom", help="Change the pop up position to bottom")
    pop_up_position_top = fields.Selection([
        ('top_left', 'Top Left'), ('top_right', 'Top Right'),
        ('top_center', 'Top Center'),
        ('full_top_container', 'Full Top Container')],
        help="Change the pop up position on top",
        string="Pop Up Position on Top", )
    pop_up_position_bottom = fields.Selection([
        ('bottom_left', 'Bottom Left'), ('bottom_right', 'Bottom Right'),
        ('bottom_center', 'Bottom Center'),
        ('full_bottom_container', 'Full Bottom Container')],
        help="Change the pop up position on bottom",
        string="Pop Up Position on Bottom", )
    accept_btn_txt = fields.Char(string="Accept button text",
                                 help="Name for the Accept button")
    reject_btn_txt = fields.Char(string="Reject button text",
                                 help="Name for the reject button")
    cookie_policy_btn = fields.Char(string="Read button text",
                                    help="Name for Cookie Policy")

    @api.model
    def _get_color(self, value):
        """Get the color code corresponding to the given value."""
        return OBJECT_COLOR.get(str(value),
                                "#FFFFFF")  # default to white if not found

    @api.onchange('is_change_pop_up_position_bottom')
    def _onchange_is_change_pop_up_position_bottom(self):
        if(self.pop_up_position_top):
            self.pop_up_position_top = ""

    @api.onchange('is_change_pop_up_position_top')
    def _onchange_is_change_pop_up_position_top(self):
        if (self.pop_up_position_bottom):
            self.pop_up_position_bottom = ""




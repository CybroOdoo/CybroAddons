# -*- coding: utf-8 -*-

#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models, fields


class ConfSettings(models.TransientModel):
    """inheriting configuration settings."""
    _inherit = "res.config.settings"

    user_password_restrict = fields.Boolean(string="Restrict User Password",
                                            default=True)
    is_strength = fields.Boolean(string="Should have 8 characters",
                                 config_parameter=
                                 'user_password_strength.is_strength')
    is_digit = fields.Boolean(string="Should have at least one number",
                              config_parameter='user_password_strength.i'
                                               's_digit')
    is_upper = fields.Boolean(string="Should have at least one uppercase",
                              config_parameter='user_password_strength.'
                                               'is_upper')
    is_lower = fields.Boolean(string="Should have at least one "
                                     "lowercase character",
                               config_parameter='user_password_strength.'
                                               'is_lower')
    is_special_symbol = fields.Boolean(string="Should have at least one "
                                              "special symbol",
                                       config_parameter='user_password_strength'
                                                        '.is_special_symbol')

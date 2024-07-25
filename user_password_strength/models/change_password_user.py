# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Farha V C (<https://www.cybrosys.com>)
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
from odoo import models, _
import re
from odoo.exceptions import UserError
from odoo.http import request


class ChangePasswordUser(models.TransientModel):
    """ Inherited model to configure users in the change password wizard. """
    _inherit = 'change.password.user'

    def change_password_button(self):
        """Overriding the password reset function"""
        for line in self:
            get_param = request.env['ir.config_parameter'].sudo().get_param
            config_strength = get_param(
                'user_password_strength.is_strength')
            config_digit = get_param('user_password_strength.is_digit')
            config_upper = get_param('user_password_strength.is_upper')
            config_lower = get_param('user_password_strength.is_lower')
            config_special_symbol = get_param('user_password_strength'
                                              '.is_special_symbol')
            if line.new_passwd:
                current_password = line.new_passwd
                if config_strength and (len(current_password) < 8):
                    raise UserError(
                        _("*****The Password Should have 8 characters."
                          ""))
                else:
                    if config_digit and (
                            re.search('[0-9]', current_password)
                            is None):
                        raise UserError(_(
                            "*****The Password Should have at least one number."))
                    if config_upper and (
                            re.search('[A-Z]', current_password)
                            is None):
                        raise UserError(_(
                            "*****The Password Should have at least "
                            "one uppercase character."))
                    if config_lower and (
                            re.search("[a-z]", current_password)
                            is None):
                        raise UserError(_(
                            "*****The Password Should have at least one "
                            "lowercase character."))
                    if config_special_symbol and \
                            (re.search("[~!@#$%^&*]",
                                       current_password) is None):
                        raise UserError(_(
                            "*****The Password Should have at least "
                            "one special symbol."))
                line.user_id._change_password(line.new_passwd)
            else:
                if (not config_strength and not
                config_digit and not config_upper and not
                config_lower and not config_special_symbol):
                    # don't keep temporary passwords in the database longer
                    # than necessary
                    self.write({'new_passwd': False})
                else:
                    raise UserError(_("The password cannot be empty."))

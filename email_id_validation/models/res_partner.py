# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jumana Haseen (<https://www.cybrosys.com>)

#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from validate_email import validate_email
from odoo import api, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Inherited module to execute a function when partner email
    record is saved"""
    _inherit = 'res.partner'

    @api.constrains('email')
    def _check_email(self):
        """
        Check the email is valid or not
        """
        if self.email:
            is_valid = validate_email(self.email, check_mx=False, verify=True,
                                      debug=False, smtp_timeout=10)
            if is_valid is not True:
                raise ValidationError(_('You can use only valid email address.'
                                        'Email address "%s" is invalid '
                                        'or does not exist') % self.email)

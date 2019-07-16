# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from validate_email import validate_email
from odoo.exceptions import ValidationError
from odoo import models, api, _


class PartnerEmailValidation(models.Model):
    _inherit = 'res.partner'

    @api.constrains('email')
    def validate(self):
        is_valid = validate_email(self.email, check_mx=False, verify=True, debug=False, smtp_timeout=10)
        if is_valid is not True:
            raise ValidationError(_('You can use only valid email address.Email address %s is invalid or does not exit')
                                  % self.email)


class EmployeeEmailValidation(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('work_email')
    def validate(self):
        is_valid = validate_email(self.work_email, check_mx=False, verify=True, debug=False, smtp_timeout=10)
        if is_valid is not True:
            raise ValidationError(_('You can use only valid email address.Email address %s is invalid or does not exit')
                                  % self.work_email)

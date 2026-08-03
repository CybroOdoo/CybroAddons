# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from email_validator import validate_email, EmailNotValidError
from odoo import api, models, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    """ Inherited module to execute a function when work_email record
     is saved"""
    _inherit = 'hr.employee'

    @api.constrains('work_email')
    def _check_email(self):
        """
        Check the work email is valid or not
        """
        for rec in self:
            if rec.work_email:
                try:
                    validate_email(
                        rec.work_email,
                        check_deliverability=True
                    )
                except EmailNotValidError as e:
                    raise ValidationError(_(
                        'Email "%(email)s" is invalid: %(reason)s') % {
                                              'email': rec.work_email,
                                              'reason': str(e), })

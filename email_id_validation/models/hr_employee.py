###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# pylint: disable=duplicate-code
from email_validator import EmailNotValidError, validate_email

from odoo import api, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    """Inherited module to validate employee work_email."""
    _inherit = 'hr.employee'

    @api.constrains('work_email')
    def _check_email(self):
        """Check whether the employee work email is valid."""
        for rec in self:
            if rec.work_email:
                try:
                    validate_email(
                        rec.work_email,
                        check_deliverability=True,
                    )
                except EmailNotValidError as e:
                    raise ValidationError(
                        rec.env._(
                            'Email "%(email)s" is invalid: %(reason)s',
                            email=rec.work_email,
                            reason=str(e),
                        ),
                    ) from e

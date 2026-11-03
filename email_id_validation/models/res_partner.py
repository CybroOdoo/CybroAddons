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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
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


class ResPartner(models.Model):
    """Inherited module to validate email when partner record is saved."""
    _inherit = 'res.partner'

    @api.constrains('email')
    def _check_email(self):
        """Check whether the partner email is valid."""
        for rec in self:
            if rec.email:
                try:
                    validate_email(
                        rec.email,
                        check_deliverability=True,
                    )
                except EmailNotValidError as e:
                    raise ValidationError(
                        rec.env._(
                            'Email "%(email)s" is invalid: %(reason)s',
                            email=rec.email,
                            reason=str(e),
                        ),
                    ) from e

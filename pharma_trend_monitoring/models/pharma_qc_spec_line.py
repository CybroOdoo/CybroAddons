# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PharmaQcSpecLine(models.Model):
    """The "watch this parameter" tick on a specification line."""
    _inherit = 'pharma.qc.spec.line'

    is_trended = fields.Boolean(
        string='Watch',
        default=False,
        copy=True,
        help='Watch this parameter: once QA approves its normal range, results '
             'outside it are flagged on the test order. Set while the '
             'specification is in draft. Only quantitative parameters can be '
             'watched.',
    )

    @api.constrains('is_trended', 'min_value', 'max_value')
    def _check_is_trended(self):
        """Qualitative parameters have nothing to trend."""
        for line in self:
            if line.is_trended and not (line.min_value or line.max_value):
                raise ValidationError(self.env._(
                    "Parameter '%s' has no numeric limit. Qualitative results "
                    "(appearance, identification, clarity) cannot be watched.",
                    line.parameter_name or self.env._('Unnamed')))

    def write(self, vals):
        """The tick changes only through a new specification version."""
        if 'is_trended' in vals:
            for line in self:
                if line.is_trended != bool(vals['is_trended']) and line.spec_id.state != 'draft':
                    raise ValidationError(self.env._(
                        "Parameter '%s': the watch setting can only be changed "
                        "while the specification is in draft.",
                        line.parameter_name or self.env._('Unnamed')))
        return super().write(vals)

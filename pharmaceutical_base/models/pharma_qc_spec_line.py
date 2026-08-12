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
from odoo.tools.translate import _


class PharmaQcSpecLine(models.Model):
    """A single test parameter within a QC specification."""
    _name = 'pharma.qc.spec.line'
    _description = 'QC Specification Parameter'
    _rec_name = 'parameter_name'
    _order = 'sequence, id'

    spec_id = fields.Many2one(
        comodel_name='pharma.qc.spec',
        string='Specification',
        required=True,
        ondelete='cascade',
        index=True,
            help='Specifies the Specification for this record.',
    )

    sequence = fields.Integer(

        string='Seq.',

        default=10,

            help='Specifies the Seq. for this record.',
    )

    parameter_name = fields.Char(
        string='Parameter',
        required=True,
        help='Name of the test parameter (e.g. Assay, Water Content, Hardness).',
    )

    test_method = fields.Char(
        string='Test Method',
        help='Method reference (e.g. HPLC, BP 2.9.1, In-house STP-QC-001).',
    )

    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit',
            help='Specifies the Unit for this record.',
    )

    min_value = fields.Float(
        string='Min. Limit',
        digits=(16, 4),
        help='Minimum acceptable value. May be zero but cannot be negative.',
    )

    max_value = fields.Float(
        string='Max. Limit',
        digits=(16, 4),
        help='Maximum acceptable value. May be zero but cannot be negative, '
             'and cannot be smaller than the Min. Limit.',
    )

    acceptance_criteria = fields.Char(
        string='Acceptance Criteria (Text)',
        help='Text-based criteria for qualitative parameters (e.g. "White crystalline powder").',
    )


    notes = fields.Char(

        string='Remarks',

            help='Specifies the Remarks for this record.',
    )

    @api.constrains('min_value', 'max_value')
    def _check_limits(self):
        """Validate that limits are non-negative and Max is not below Min."""
        for line in self:
            if line.min_value < 0 or line.max_value < 0:
                raise ValidationError(_(
                    "Parameter '%s': Min. Limit and Max. Limit cannot be "
                    "negative.", line.parameter_name or _('Unnamed')))
            if line.max_value < line.min_value:
                raise ValidationError(_(
                    "Parameter '%s': Max. Limit (%s) cannot be smaller than "
                    "Min. Limit (%s).",
                    line.parameter_name or _('Unnamed'),
                    line.max_value, line.min_value))

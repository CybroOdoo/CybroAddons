# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields


class UniversityAdmissionRound(models.Model):
    """Represents an admission round (e.g. Early Decision, Regular Decision)
    with its deadlines, decision dates and binding status shown on the
    website."""
    _name = 'university.admission.round'
    _description = 'University Admission Round'
    _order = 'sequence, id'

    name = fields.Char('Round Name', required=True, translate=True,
                       help='Name of the admission round (e.g. Early Decision, Regular Decision).')
    deadline_date_str = fields.Char('Deadline Date', required=True, translate=True,
                                    help='Application deadline for this round, shown as free text.')
    decision_date_str = fields.Char('Decision By', required=True, translate=True,
                                    help='Date by which applicants will receive an admission decision.')
    notes = fields.Char('Notes', translate=True,
                        help='Additional notes or remarks about this admission round.')
    sequence = fields.Integer('Sequence', default=10,
                              help='Determines the display order of rounds. Lower values appear first.')
    is_binding = fields.Boolean('Binding Round', default=False,
                                help='Check if this round is binding, meaning applicants must enroll if admitted.')

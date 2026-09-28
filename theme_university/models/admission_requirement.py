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


class UniversityAdmissionRequirement(models.Model):
    """Represents a single admission requirement that can be linked to one or
    more application types and displayed to prospective applicants."""
    _name = 'university.admission.requirement'
    _description = 'University Admission Requirement'
    _order = 'sequence, id'

    name = fields.Char('Requirement Name', required=True, translate=True,
                       help='Name of the admission requirement displayed to applicants.')
    sequence = fields.Integer('Sequence', default=10,
                              help='Determines the display order of requirements. Lower values appear first.')

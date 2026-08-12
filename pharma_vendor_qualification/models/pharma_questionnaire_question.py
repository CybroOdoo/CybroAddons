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

from odoo import fields, models

class PharmaQuestionnaireQuestion(models.Model):
    """Model to define individual questions within a questionnaire template."""
    _name = 'pharma.questionnaire.question'
    _description = 'Questionnaire Question'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        comodel_name='pharma.questionnaire.template',
        string='Template',
        required=True,
        ondelete='cascade',
        index=True,
            help='Specifies the Template for this record.',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
            help='Specifies the Sequence for this record.',
    )
    section = fields.Char(
        string='Section',
        help='Used to group questions together (e.g., "Quality Management", "Facilities").',
        translate=True
    )
    question_text = fields.Char(
        string='Question',
        required=True,
        translate=True,
            help='Specifies the Question for this record.',
    )
    answer_type = fields.Selection(
        selection=[
            ('yes_no', 'Yes / No'),
            ('text', 'Text'),
            ('number', 'Number'),
            ('file', 'Upload file'),
        ],
        string='Answer Type',
        required=True,
        default='yes_no',
            help='Specifies the Answer Type for this record.',
    )

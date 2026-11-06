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
from odoo import fields, models


class PharmaQuestionnaireQuestion(models.Model):
    """Model to define individual questions within a questionnaire template."""
    _name = 'pharma.questionnaire.question'
    _description = 'Questionnaire Question'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        comodel_name='pharma.questionnaire.template',
        required=True,
        ondelete='cascade',
        index=True,
        help='Questionnaire template this question belongs to.',
    )
    sequence = fields.Integer(
        default=10,
        help='Order of the question within its template.',
    )
    section = fields.Char(
        help='Used to group questions together (e.g., "Quality Management", "Facilities").',
        translate=True
    )
    question_text = fields.Char(
        string='Question',
        required=True,
        translate=True,
        help='Question shown to the vendor on the portal.',
    )
    answer_type = fields.Selection(
        selection=[
            ('yes_no', 'Yes / No'),
            ('text', 'Text'),
            ('number', 'Number'),
            ('file', 'Upload file'),
        ],
        required=True,
        default='yes_no',
        help='How the vendor answers: yes/no, text, number or a file upload.',
    )

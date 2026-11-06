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


class PharmaQuestionnaireTemplate(models.Model):
    """Model to define templates for vendor qualification questionnaires."""
    _name = 'pharma.questionnaire.template'
    _description = 'Questionnaire Template'
    _order = 'name'

    name = fields.Char(
        string='Template Name',
        required=True,
        translate=True,
        help='Name of the questionnaire template.',
    )
    description = fields.Text(
        translate=True,
        help='What the questionnaire covers and when to use it.',
    )
    active = fields.Boolean(
        default=True,
        help="Set to False to hide this template without removing it.",
    )
    question_ids = fields.One2many(
        comodel_name='pharma.questionnaire.question',
        inverse_name='template_id',
        string='Questions',
        copy=True,
        help='Questions sent to the vendor with this template.',
    )

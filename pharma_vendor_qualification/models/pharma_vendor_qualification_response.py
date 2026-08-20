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


class PharmaVendorQualificationResponse(models.Model):
    """Model to store a vendor's response to a specific qualification question."""
    _name = 'pharma.vendor.qualification.response'
    _description = 'Vendor Qualification Response'
    _order = 'sequence, id'

    qualification_id = fields.Many2one(
        comodel_name='pharma.vendor.qualification',
        string='Vendor Qualification',
        required=True,
        ondelete='cascade',
        index=True,
        help='Specifies the Vendor Qualification for this record.',
    )
    question_id = fields.Many2one(
        comodel_name='pharma.questionnaire.question',
        string='Question Reference',
        required=True,
        ondelete='restrict',
        help='Specifies the Question Reference for this record.',
    )
    # Display fields related to the question
    section = fields.Char(
        related='question_id.section',
        string='Section',
        readonly=True,
        help='Specifies the Section for this record.',
    )
    sequence = fields.Integer(
        related='question_id.sequence',
        string='Sequence',
        readonly=True,
        help='Specifies the Sequence for this record.',
    )
    question_text = fields.Char(
        related='question_id.question_text',
        string='Question',
        readonly=True,
        help='Specifies the Question for this record.',
    )
    answer_type = fields.Selection(
        related='question_id.answer_type',
        string='Answer Type',
        readonly=True,
        help='Specifies the Answer Type for this record.',
    )
    # Answer fields
    answer_yes_no = fields.Selection(
        selection=[('yes', 'Yes'), ('no', 'No')],
        string='Yes/No Answer',
        help='Specifies the Yes/No Answer for this record.',
    )
    answer_text = fields.Text(
        string='Text Answer',
        help='Specifies the Text Answer for this record.',
    )
    answer_number = fields.Float(
        string='Number Answer',
        help='Specifies the Number Answer for this record.',
    )
    answer_file = fields.Binary(
        string='File',
        attachment=True,
        help='File uploaded by the vendor as an answer to this question.',
    )
    answer_file_filename = fields.Char(
        string='File Answer Filename',
        help='Original filename of the file uploaded by the vendor.',
    )

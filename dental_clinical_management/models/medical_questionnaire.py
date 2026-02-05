# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class MedicalQuestionnaire(models.Model):
    """Medical questions to be asked to the patients while their appointment"""
    _name = 'medical.questionnaire'
    _description = 'Medical Questionnaire'

    question_id = fields.Many2one('medical.questions',
                                  string='Questions',
                                  help="All added question")
    yes_no = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                              string='Yes or No', help="")
    reason = fields.Text(string='Reason', help="Reason for the question answer")
    patient_id = fields.Many2one('res.partner',
                                 string='Patient',
                                 help="Patient name")

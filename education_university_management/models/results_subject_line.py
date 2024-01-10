# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResultsSubjectLine(models.Model):
    """Used to manage subject details of student exam result"""
    _name = 'results.subject.line'
    _description = 'Results Subject Line'

    name = fields.Char(string='Name', help="Name of the result")
    subject_id = fields.Many2one('university.subject',
                                 string='Subject',
                                 help="Subjects of the exam")
    max_mark = fields.Float(string='Max Mark', help="Maximum mark of subject")
    pass_mark = fields.Float(string='Pass Mark',
                             help="Pass mark of the subject")
    mark_scored = fields.Float(string='Mark Scored',
                               help="Marks scored by the students in subjects")
    is_pass = fields.Boolean(string='Pass/Fail',
                             help="Enable if the student "
                                  "pass the subject")
    result_id = fields.Many2one('exam.result', string='Result Id',
                                help="Relation to result model")

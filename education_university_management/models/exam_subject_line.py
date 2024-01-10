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


class ExamSubjectLine(models.Model):
    """For managing the subjects in the exam"""
    _name = 'exam.subject.line'
    _description = 'Subject Line of Exam'

    subject_id = fields.Many2one('university.subject',
                                 string='Subject', required=True,
                                 help="Select subjects of exam")
    date = fields.Date(string='Date', required=True,
                       help="Select date of the subject")
    time_from = fields.Float(string='Time From', required=True,
                             help="Enter starting time of the subject")
    time_to = fields.Float(string='Time To', required=True,
                           help="Enter ending time of the subject")
    mark = fields.Integer(string='Mark', help="Enter mark for the subject")
    exam_id = fields.Many2one('university.exam', string='Exam',
                              help="Relation to exam model")
    company_id = fields.Many2one(
        'res.company', string='Company', help="Company of the exam",
        default=lambda self: self.env.company)

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
from odoo import api, fields, models


class ExamResult(models.Model):
    """Creating a model for storing students exam result."""
    _name = 'exam.result'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Exam Result"

    name = fields.Char(string='Name', help="Name of the exam result")
    exam_id = fields.Many2one('university.exam', string='Exam',
                              help="Which exam does this result belong to")
    batch_id = fields.Many2one('university.batch', string='Batch',
                               help="Which batch does this result belong to")
    student_id = fields.Many2one('university.student',
                                 string='Student', help="Result of student")
    subject_line_ids = fields.One2many('results.subject.line',
                                       'result_id',
                                       help="Result of each subject in exam",
                                       string='Subjects')
    academic_year_id = fields.Many2one(related='batch_id.academic_year_id',
                                       help="Academic year of the batch",
                                       string='Academic Year')
    company_id = fields.Many2one(
        'res.company', string='Company', help="Which company's "
                                              "result is",
        default=lambda self: self.env.company)
    total_pass_mark = fields.Float(string='Total Pass Mark', store=True,
                                   help="Total mark to pass the exam",
                                   readonly=True, compute='_total_marks_all')
    total_max_mark = fields.Float(string='Total Max Mark', store=True,
                                  help="Maximum mark of the exam",
                                  readonly=True,
                                  compute='_compute_total_marks')
    total_mark_scored = fields.Float(string='Total Marks Scored', store=True,
                                     help="Total mark scored by student",
                                     readonly=True,
                                     compute='_compute_total_marks')
    is_overall_pass = fields.Boolean(string='Overall Pass/Fail', store=True,
                                     help="Overall pass or fail ratio",
                                     readonly=True,
                                     compute='_compute_total_marks')

    @api.depends('subject_line_ids.mark_scored')
    def _compute_total_marks(self):
        """This method is for computing total mark scored and overall
                    pass details"""
        for results in self:
            total_pass_mark = 0
            total_max_mark = 0
            total_mark_scored = 0
            is_overall_pass = True
            for subjects in results.subject_line_ids:
                total_pass_mark += subjects.pass_mark
                total_max_mark += subjects.max_mark
                total_mark_scored += subjects.mark_scored
                if not subjects.is_pass:
                    is_overall_pass = False
            results.total_pass_mark = total_pass_mark
            results.total_max_mark = total_max_mark
            results.total_mark_scored = total_mark_scored
            results.is_overall_pass = is_overall_pass

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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ExamValuation(models.Model):
    """Used to manage the valuation of exams"""
    _name = 'exam.valuation'
    _description = "Exam Valuation"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default='New', help="Name of the record")
    exam_id = fields.Many2one('university.exam', string='Exam',
                              required=True, help="Select exam for valuation",
                              domain=[('state', '=', 'ongoing')])
    batch_id = fields.Many2one(related='exam_id.batch_id', string='Batch',
                               help="Choose the batch that you want to"
                                    " evaluate", required=True)
    evaluator_id = fields.Many2one('university.faculty',
                                   string='Evaluator',
                                   help="Select a valuation evaluator")
    mark = fields.Float(string='Max Mark',
                        help="Maximum mark of the selected subject",
                        required=True)
    pass_mark = fields.Float(string='Pass Mark',
                             help="Mark needed to pass the exam ",
                             required=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('completed', 'Completed'),
                              ('cancel', 'Canceled')], default='draft',
                             help="Status of the valuation")
    valuation_line_ids = fields.One2many('exam.valuation.line',
                                         'valuation_id',
                                         help="Students valuation details",
                                         string='Students')
    subject_id = fields.Many2one('university.subject',
                                 string='Subject',
                                 help="Choose subject of the exam for "
                                      "valuation", required=True)
    subject_ids = fields.Many2many('university.subject',
                                   string="Subjects",
                                   help="Subjects under the exam",
                                   compute="_compute_subject_ids")
    is_mark_sheet_created = fields.Boolean(string='Mark sheet Created',
                                           help="Enable if a mark sheet for "
                                                "the students in the batch is "
                                                "created or not")
    date = fields.Date(string='Date', default=fields.Date.today,
                       help="Date of the valuation")
    academic_year_id = fields.Many2one(related='batch_id.academic_year_id',
                                       string='Academic Year',
                                       help="Academic year of the selected "
                                            "batch")
    company_id = fields.Many2one(
        'res.company', string='Company',
        help="Company of the valuation", default=lambda self: self.env.company)

    def action_create_mark_sheet(self):
        """Button action for creating marksheet of students"""
        students = self.batch_id.batch_student_ids
        if len(students) < 1:
            raise UserError(_('There are no students in this Batch'))
        self.env['exam.valuation.line'].create(({'student_id': student.id,
                                                 'valuation_id': self.id,
                                                 }) for student in students)
        self.is_mark_sheet_created = True

    @api.model
    def create(self, vals):
        """ This method overrides the create method to check if the exam
            valuation with respect to the subject and batch has already
            been completed.

            :param vals (dict): Dictionary containing the field values for
                                the new exam valuation record.
            :returns class:`exam.valuation`The created exam valuation record.
            :raises UserError: If a valuation sheet for the specified subject,
                               division, and exam already exists.
        """
        res = super(ExamValuation, self).create(vals)
        search_valuation = self.env['exam.valuation'].search(
            [('exam_id', '=', res.exam_id.id),
             ('batch_id', '=', res.batch_id.id),
             ('subject_id', '=', res.subject_id.id),
             ('state', '!=', 'cancel')])
        if len(search_valuation) > 1:
            raise UserError(
                _('Valuation Sheet for \n Subject --> %s \nDivision --> %s '
                  '\nExam --> %s \n is already created') % (
                    res.subject_id.name, res.batch_id.name,
                    res.exam_id.name))
        return res

    @api.depends('exam_id')
    def _compute_subject_ids(self):
        """ To find the subjects in the selected exam and assign them
            to subject_ids field for setting domain for subject_id field.
        """
        for rec in self:
            rec.subject_ids = rec.exam_id.subject_line_ids.subject_id \
                if rec.exam_id else False

    def action_valuation_completed(self):
        """Method for completing the valuation and also creating the exam
          result with the valuation line and verify whether or not the exam
          with the subject and the student already exists; if not, a new exam
          result will be created."""
        self.name = str(self.exam_id.name)
        result_obj = self.env['exam.result']
        result_line_obj = self.env['results.subject.line']
        for students in self.valuation_line_ids:
            search_result = result_obj.search(
                [('exam_id', '=', self.exam_id.id),
                 ('batch_id', '=', self.batch_id.id),
                 ('student_id', '=', students.student_id.id)])
            if len(search_result) < 1:
                result_data = {
                    'name': self.name,
                    'exam_id': self.exam_id.id,
                    'batch_id': self.batch_id.id,
                    'student_id': students.student_id.id,
                }
                result = result_obj.create(result_data)
                result_line_data = {
                    'name': self.name,
                    'subject_id': self.subject_id.id,
                    'max_mark': self.mark,
                    'pass_mark': self.pass_mark,
                    'mark_scored': students.mark_scored,
                    'is_pass': students.is_pass,
                    'result_id': result.id,
                }
                result_line_obj.create(result_line_data)
            else:
                result_line_data = {
                    'subject_id': self.subject_id.id,
                    'max_mark': self.mark,
                    'pass_mark': self.pass_mark,
                    'mark_scored': students.mark_scored,
                    'is_pass': students.is_pass,
                    'result_id': search_result.id,
                }
                result_line_obj.create(result_line_data)
        self.state = 'completed'

    def action_set_to_draft(self):
        """Method to set the record to the draft stage,
                and it will unlink all exam results with this valuation."""
        for students in self.valuation_line_ids:
            search_result = self.env['exam.result'].search(
                [('exam_id', '=', self.exam_id.id),
                 ('batch_id', '=', self.batch_id.id),
                 ('student_id', '=', students.student_id.id)])
            search_result_line = self.env['results.subject.line'].search(
                [('result_id', '=', search_result.id),
                 ('subject_id', '=', self.subject_id.id)])
            search_result_line.unlink()
            search_result.unlink()
        self.state = 'draft'

    def action_cancel_valuation(self):
        """Action to cancel the valuation"""
        self.state = 'cancel'

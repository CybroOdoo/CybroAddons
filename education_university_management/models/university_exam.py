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
from odoo.exceptions import UserError, ValidationError


class UniversityExam(models.Model):
    """Used to manage student exams of every semester"""
    _name = 'university.exam'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "University Student Exam management"

    name = fields.Char(string='Name', default='New', help="Name of the exam")
    batch_id = fields.Many2one('university.batch', string='Batch',
                               help="Which batch's exam is")
    exam_type_id = fields.Many2one('university.exam.type',
                                   string='Type', help="Type of exam",
                                   required=True)
    start_date = fields.Date(string='Start Date', required=True,
                             help="Enter start date of the exam")
    end_date = fields.Date(string='End Date', required=True,
                           help="Enter end date of the exam")
    subject_line_ids = fields.One2many('exam.subject.line',
                                       'exam_id', string='Subjects',
                                       help="Subjects of the exam")
    state = fields.Selection(
        [('draft', 'Draft'),
         ('ongoing', 'On Going'),
         ('close', 'Closed'),
         ('cancel', 'Canceled')],
        default='draft', help="Status of the exam")
    academic_year_id = fields.Many2one(related='batch_id.academic_year_id',
                                       string='Academic Year',
                                       help="Academic year of batch")
    company_id = fields.Many2one(
        'res.company', string='Company', help="Company of the exam",
        default=lambda self: self.env.company)

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        """ This constraint method validates that the start date of the exam is
             earlier than the end date.
            :raises ValidationError: If the start date is greater than the
                                     end date
       """
        for rec in self:
            if rec.start_date > rec.end_date:
                raise ValidationError(
                    _("Start date must be Anterior to end date"))

    def action_close_exam(self):
        """ This method sets the state of the exam to 'close',
            indicating that the exam has been closed.
        """
        self.state = 'close'

    def action_cancel_exam(self):
        """ This method sets the state of the exam to 'cancel',
            indicating that the exam has been canceled.
        """
        self.state = 'cancel'

    def action_confirm_exam(self):
        """ This method confirms the exam and checks if at least
            one subject is added to the exam.
            :raises UserError: If no subjects are added to the exam.
        """
        if len(self.subject_line_ids) < 1:
            raise UserError(_('Please Add Subjects'))
        self.name = str(self.exam_type_id.name) + '/' + str(self.start_date)[
                                                        0:10] + ' (' + str(
            self.batch_id.name) + ')'
        self.state = 'ongoing'

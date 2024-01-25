# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class QuestionDuplicate(models.TransientModel):
    """
    The ActionWizard class is creating questions for the selected surveys.
        Methods:
            action_add_survey(self):
                creating new records for the selected surveys
                while clicking "action_add_survey" button.
    """
    _name = "question.duplicate"
    _description = "Question Duplicate"

    survey_ids = fields.Many2many('survey.survey', string="Surveys",
                                  help="Select the survey to duplicate the"
                                       " question")

    def action_check_survey(self):
        """
        Summery:
            Checking the surveys selected showing exception or creating record
            by calling the "creating_questions" method  while clicking
            "action_add_survey" button.
        """
        if self.survey_ids:
            question_ids = self._context.get('active_ids')
            flag = 0
            for question_id in question_ids:
                for survey_id in self.survey_ids:
                    question = self.env['survey.question'].browse(question_id)
                    selected_question = self.env['survey.question'].search(
                        [('survey_id', '=', survey_id.id), ('title', '=', question.title)])
                    if selected_question:
                        flag = 1
            if flag == 1:
                raise ValidationError(
                    _("The selected question is already included in the"
                      " survey."))
            else:
                self.create_question()
        else:
            raise ValidationError(_("Please Select The Surveys"))

    def create_question(self):
        """
        Summery:
           creating new records for the selected surveys while calling in the
           "action_add_survey" method.
        """
        question_ids = self._context.get('active_ids')
        for question_id in question_ids:
            survey_question_id = self.env['survey.question'].browse(question_id)
            for survey_id in self.survey_ids:
                question_vals = {
                    'survey_id': survey_id.id,
                    'title': survey_question_id.title,
                    'question_type': survey_question_id.question_type,
                    'description': survey_question_id.description,
                    'comments_allowed': survey_question_id.comments_allowed,
                    'constr_mandatory': survey_question_id.constr_mandatory,
                    'constr_error_msg': survey_question_id.constr_error_msg,
                    'triggering_answer_ids': survey_question_id.triggering_answer_ids,
                    'is_time_limited': survey_question_id.is_time_limited,
                    'question_placeholder': survey_question_id.question_placeholder,
                    'validation_required': survey_question_id.validation_required,
                    'matrix_subtype': survey_question_id.matrix_subtype,
                }
                question = self.env['survey.question'].sudo().create(
                    question_vals)
                answer_ids = survey_question_id.suggested_answer_ids.filtered(
                    lambda r: r.value)
                answer_vals = answer_ids.mapped(lambda r: {
                    'question_id': question.id,
                    'value': r.value,
                    'is_correct': r.is_correct,
                    'answer_score': r.answer_score,
                    'value_image': r.value_image,
                })
                self.env['survey.question.answer'].sudo().create(answer_vals)

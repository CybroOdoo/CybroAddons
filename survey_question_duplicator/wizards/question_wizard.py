# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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


class QuestionWizard(models.TransientModel):
    """
    The ActionWizard class is creating questions for the selected surveys.
        Methods:
            action_add_survey(self):
                creating new records for the selected surveys
                while clicking "action_add_survey" button.
    """
    _name = "question.wizard"
    _description = "Question Wizard"

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
                    selected_question = self.env['survey.question'].browse(
                        question_id).survey_id.id
                    if selected_question == survey_id.id:
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
                    'is_conditional': survey_question_id.is_conditional,
                    'constr_mandatory': survey_question_id.constr_mandatory,
                    'is_time_limited': survey_question_id.is_time_limited,
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

# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
from odoo import fields, models


class SurveySelector(models.TransientModel):
    """Wizard for selecting the surveys to which questions to be added"""
    _name = "survey.selector"
    _description = "Survey Selector"

    survey_ids = fields.Many2many('survey.survey', string="Surveys",
                                  help="Select the surveys to which the"
                                       " questions to be added", required=True)

    def action_add_to_survey(self):
        """Method for adding the questions to the selected surveys if the
        question not already included."""
        for question_id in self._context.get('active_ids'):
            for survey in self.survey_ids:
                question = self.env['survey.question'].browse(question_id)
                if [survey, question.title,
                    question.question_type,
                    question.suggested_answer_ids.mapped('value')] not in [
                    [survey, rec.title, rec.question_type,
                     rec.suggested_answer_ids.mapped('value')] for
                    rec in
                    survey.question_and_page_ids]:
                    survey_question = self.env['survey.question'].sudo(
                    ).create({
                        'survey_id': survey.id,
                        'title': question.title,
                        'question_type': question.question_type,
                        'description': question.description,
                        'comments_allowed': question.comments_allowed,
                        'is_conditional': question.is_conditional,
                        'constr_mandatory': question.constr_mandatory,
                        'is_time_limited': question.is_time_limited,
                    })
                    self.env['survey.question.answer'].sudo().create(
                        question.suggested_answer_ids.filtered(
                            lambda r: r.value).mapped(lambda r: {
                            'question_id': survey_question.id,
                            'value': r.value,
                            'is_correct': r.is_correct,
                            'answer_score': r.answer_score,
                            'value_image': r.value_image,
                        }))

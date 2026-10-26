# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import Command, fields, models, _
from odoo.exceptions import ValidationError


class QuestionDuplicate(models.TransientModel):
    """Wizard for copying selected questions to other surveys."""
    _name = "question.duplicate"
    _description = "Question Duplicate"

    survey_ids = fields.Many2many(
        'survey.survey',
        string="Surveys",
        help="Select the surveys where the questions should be copied.",
    )

    def action_check_survey(self):
        """Validate the selection and duplicate the selected questions."""
        if not self.survey_ids:
            raise ValidationError(_("Please select at least one survey."))
        questions = self._get_active_questions()
        if not questions:
            raise ValidationError(_("Please select at least one question."))

        for survey in self.survey_ids:
            titles = questions.mapped('title')
            existing_titles = set(self.env['survey.question'].search([
                ('survey_id', '=', survey.id),
                ('title', 'in', titles),
            ]).mapped('title'))
            if existing_titles:
                raise ValidationError(_(
                    "The following selected question(s) already exist in "
                    "%(survey)s: %(questions)s",
                    survey=survey.display_name,
                    questions=', '.join(sorted(existing_titles)),
                ))
            if len(titles) != len(set(titles)):
                raise ValidationError(_(
                    "Selected questions must have unique titles to be "
                    "duplicated into the same survey."
                ))
        self.create_question()

    def _get_active_questions(self):
        """Return selected questions, validating that the ids still exist."""
        question_ids = self.env.context.get('active_ids', [])
        questions = self.env['survey.question'].browse(question_ids).exists()
        if len(questions) != len(set(question_ids)):
            raise ValidationError(_("One or more selected questions no longer exist."))
        return questions

    def create_question(self):
        """Copy selected questions and their copyable settings to each survey."""
        questions = self._get_active_questions()
        for survey in self.survey_ids:
            copied_by_source = {}
            for source in questions:
                copied_by_source[source.id] = source.copy({
                    'survey_id': survey.id,
                    'triggering_answer_ids': [Command.clear()],
                })

            copied_answer_ids = {
                source_answer.id: copied_answer.id
                for source in questions
                for source_answer, copied_answer in zip(
                    source.suggested_answer_ids,
                    copied_by_source[source.id].suggested_answer_ids.sorted(),
                )
            }
            for source in questions:
                copied = copied_by_source[source.id]
                trigger_ids = []
                for source_answer in source.triggering_answer_ids:
                    source_trigger_question = source_answer.question_id
                    if source_trigger_question.id in copied_by_source:
                        trigger_ids.append(copied_answer_ids[source_answer.id])
                        continue
                    target_trigger_question = self.env['survey.question'].search([
                        ('survey_id', '=', survey.id),
                        ('title', '=', source_trigger_question.title),
                        ('is_page', '=', False),
                    ], limit=1)
                    target_answer = target_trigger_question.suggested_answer_ids.filtered(
                        lambda answer: answer.value == source_answer.value
                    )[:1]
                    if not target_answer:
                        raise ValidationError(_(
                            "Cannot copy the condition for '%(question)s': "
                            "the triggering question or answer is missing in "
                            "survey '%(survey)s'.",
                            question=source.title,
                            survey=survey.display_name,
                        ))
                    trigger_ids.append(target_answer.id)
                copied.triggering_answer_ids = [Command.set(trigger_ids)]

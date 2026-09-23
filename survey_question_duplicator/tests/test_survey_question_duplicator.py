# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSurveyQuestionDuplicator(TransactionCase):
    """Test copying survey questions through the duplicate-question wizard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source_survey = cls.env['survey.survey'].create({
            'title': 'Source Survey',
        })
        cls.target_survey = cls.env['survey.survey'].create({
            'title': 'Target Survey',
        })

    def _create_question(self, survey, title='Which option is correct?'):
        return self.env['survey.question'].create({
            'survey_id': survey.id,
            'title': title,
            'question_type': 'simple_choice',
            'description': '<p>Select one option.</p>',
            'comments_allowed': True,
            'constr_mandatory': True,
            'constr_error_msg': 'An answer is required.',
            'question_placeholder': 'Choose an option',
            'suggested_answer_ids': [
                (0, 0, {
                    'value': 'Correct answer',
                    'is_correct': True,
                    'answer_score': 5,
                }),
                (0, 0, {
                    'value': 'Incorrect answer',
                    'is_correct': False,
                    'answer_score': -1,
                }),
            ],
        })

    def _create_wizard(self, question, surveys=None):
        surveys = surveys or self.env['survey.survey']
        return self.env['question.duplicate'].with_context(
            active_ids=question.ids,
        ).create({
            'survey_ids': [(6, 0, surveys.ids)],
        })

    def test_action_add_question_opens_duplicate_wizard(self):
        question = self._create_question(self.source_survey)

        action = question.action_add_question()

        self.assertEqual(action, {
            'name': 'Add To Survey',
            'view_mode': 'form',
            'res_model': 'question.duplicate',
            'type': 'ir.actions.act_window',
            'target': 'new',
        })

    def test_duplicate_question_copies_question_and_answers(self):
        source_question = self._create_question(self.source_survey)
        wizard = self._create_wizard(source_question, self.target_survey)

        wizard.action_check_survey()

        duplicated_question = self.env['survey.question'].search([
            ('survey_id', '=', self.target_survey.id),
            ('title', '=', source_question.title),
        ])
        self.assertEqual(len(duplicated_question), 1)
        self.assertEqual(duplicated_question.question_type,
                         source_question.question_type)
        self.assertEqual(duplicated_question.description,
                         source_question.description)
        self.assertEqual(duplicated_question.comments_allowed,
                         source_question.comments_allowed)
        self.assertEqual(duplicated_question.constr_mandatory,
                         source_question.constr_mandatory)
        self.assertEqual(duplicated_question.constr_error_msg,
                         source_question.constr_error_msg)
        self.assertEqual(
            duplicated_question.suggested_answer_ids.mapped('value'),
            ['Correct answer', 'Incorrect answer'],
        )
        self.assertEqual(
            duplicated_question.suggested_answer_ids.mapped('is_correct'),
            [True, False],
        )
        self.assertEqual(
            duplicated_question.suggested_answer_ids.mapped('answer_score'),
            [5, -1],
        )

    def test_duplicate_question_requires_a_target_survey(self):
        question = self._create_question(self.source_survey)
        wizard = self._create_wizard(question)

        with self.assertRaisesRegex(ValidationError, 'Please Select The Surveys'):
            wizard.action_check_survey()

    def test_duplicate_question_rejects_existing_question_in_target(self):
        source_question = self._create_question(self.source_survey)
        self._create_question(self.target_survey, source_question.title)
        wizard = self._create_wizard(source_question, self.target_survey)

        with self.assertRaisesRegex(
            ValidationError, 'The selected question is already included in the survey.',
        ):
            wizard.action_check_survey()

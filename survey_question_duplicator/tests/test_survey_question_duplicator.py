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
from odoo import Command
from odoo.tests import common
from odoo.exceptions import ValidationError


class TestSurveyQuestionDuplicator(common.TransactionCase):
    """Test cases for Survey Question Duplicator module"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test surveys
        cls.survey_1 = cls.env['survey.survey'].create({
            'title': 'Test Survey 1',
        })
        cls.survey_2 = cls.env['survey.survey'].create({
            'title': 'Test Survey 2',
        })
        # Create test question in survey_1
        cls.question_1 = cls.env['survey.question'].create({
            'survey_id': cls.survey_1.id,
            'title': 'Test Question 1',
            'question_type': 'simple_choice',
            'description': 'Test description',
            'comments_allowed': True,
            'constr_mandatory': True,
            'constr_error_msg': 'This field is required',
        })
        # Create suggested answers for the question
        cls.answer_1 = cls.env['survey.question.answer'].create({
            'question_id': cls.question_1.id,
            'value': 'Option 1',
            'is_correct': True,
            'answer_score': 10,
        })
        cls.answer_2 = cls.env['survey.question.answer'].create({
            'question_id': cls.question_1.id,
            'value': 'Option 2',
            'is_correct': False,
            'answer_score': 0,
        })

    def test_action_add_question(self):
        """Test that action_add_question returns correct wizard action"""
        action = self.question_1.action_add_question()
        self.assertEqual(action['name'], "Add to Survey")
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['res_model'], 'question.duplicate')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(action['context']['active_ids'], [self.question_1.id])

    def test_action_check_survey_no_survey_selected(self):
        """Test that ValidationError is raised when no survey is selected"""
        wizard = self.env['question.duplicate'].create({
            'survey_ids': False,
        })
        with self.assertRaises(ValidationError) as cm:
            wizard.with_context(active_ids=[self.question_1.id]).action_check_survey()
        self.assertIn("Please select at least one survey", str(cm.exception))

    def test_action_check_survey_duplicate_question(self):
        """Test that ValidationError is raised when question already exists in survey"""
        # First, duplicate the question to survey_2
        wizard = self.env['question.duplicate'].create({
            'survey_ids': [Command.set([self.survey_2.id])],
        })
        wizard.with_context(active_ids=[self.question_1.id]).action_check_survey()
        
        # Try to duplicate the same question again - should raise ValidationError
        wizard_2 = self.env['question.duplicate'].create({
            'survey_ids': [Command.set([self.survey_2.id])],
        })
        with self.assertRaises(ValidationError) as cm:
            wizard_2.with_context(active_ids=[self.question_1.id]).action_check_survey()
        self.assertIn("already exist in", str(cm.exception))

    def test_create_question(self):
        """Test that question is duplicated correctly to target survey"""
        wizard = self.env['question.duplicate'].create({
            'survey_ids': [Command.set([self.survey_2.id])],
        })
        wizard.with_context(active_ids=[self.question_1.id]).create_question()
        
        # Verify question was created in survey_2
        duplicated_question = self.env['survey.question'].search([
            ('survey_id', '=', self.survey_2.id),
            ('title', '=', 'Test Question 1')
        ], limit=1)
        self.assertTrue(duplicated_question)
        self.assertEqual(duplicated_question.question_type, 'simple_choice')
        self.assertEqual(duplicated_question.description, 'Test description')
        self.assertTrue(duplicated_question.comments_allowed)
        self.assertTrue(duplicated_question.constr_mandatory)
        self.assertEqual(duplicated_question.constr_error_msg, 'This field is required')
        
        # Verify suggested answers were duplicated
        answers = self.env['survey.question.answer'].search([
            ('question_id', '=', duplicated_question.id)
        ])
        self.assertEqual(len(answers), 2)
        answer_values = answers.mapped('value')
        self.assertIn('Option 1', answer_values)
        self.assertIn('Option 2', answer_values)

    def test_create_question_multiple_surveys(self):
        """Test that question is duplicated to multiple surveys"""
        survey_3 = self.env['survey.survey'].create({
            'title': 'Test Survey 3',
        })
        wizard = self.env['question.duplicate'].create({
            'survey_ids': [Command.set([self.survey_2.id, survey_3.id])],
        })
        wizard.with_context(active_ids=[self.question_1.id]).create_question()
        
        # Verify question was created in both surveys
        for survey in [self.survey_2, survey_3]:
            duplicated_question = self.env['survey.question'].search([
                ('survey_id', '=', survey.id),
                ('title', '=', 'Test Question 1')
            ], limit=1)
            self.assertTrue(duplicated_question)

    def test_create_question_multiple_questions(self):
        """Test that multiple questions can be duplicated"""
        question_2 = self.env['survey.question'].create({
            'survey_id': self.survey_1.id,
            'title': 'Test Question 2',
            'question_type': 'text_box',
        })
        wizard = self.env['question.duplicate'].create({
            'survey_ids': [Command.set([self.survey_2.id])],
        })
        wizard.with_context(active_ids=[self.question_1.id, question_2.id]).create_question()
        
        # Verify both questions were created in survey_2
        questions_in_survey_2 = self.env['survey.question'].search([
            ('survey_id', '=', self.survey_2.id)
        ])
        self.assertEqual(len(questions_in_survey_2), 2)
        titles = questions_in_survey_2.mapped('title')
        self.assertIn('Test Question 1', titles)
        self.assertIn('Test Question 2', titles)

    def test_create_question_with_all_fields(self):
        """Test that copyable question settings are duplicated."""
        # Create a question with more fields
        question_full = self.env['survey.question'].create({
            'survey_id': self.survey_1.id,
            'title': 'Full Question',
            'question_type': 'char_box',
            'description': 'Full description',
            'comments_allowed': True,
            'comments_message': 'Add a comment',
            'comment_count_as_answer': True,
            'constr_mandatory': True,
            'constr_error_msg': 'Error message',
            'is_time_limited': True,
            'time_limit': 45,
            'question_placeholder': 'Placeholder text',
            'validation_required': True,
            'validation_length_min': 2,
            'validation_length_max': 20,
            'validation_error_msg': 'Please enter a valid response',
            'validation_email': True,
            'save_as_email': True,
            'scale_min': 1,
            'scale_max': 5,
            'scale_min_label': 'Low',
            'scale_max_label': 'High',
        })
        matrix_question = self.env['survey.question'].create({
            'survey_id': self.survey_1.id,
            'title': 'Matrix Question',
            'question_type': 'matrix',
            'matrix_subtype': 'multiple',
            'matrix_row_ids': [Command.create({'value': 'Row 1'})],
            'suggested_answer_ids': [Command.create({'value': 'Column 1'})],
        })
        
        wizard = self.env['question.duplicate'].create({
            'survey_ids': [Command.set([self.survey_2.id])],
        })
        wizard.with_context(active_ids=[
            question_full.id, matrix_question.id,
        ]).create_question()
        
        duplicated_question = self.env['survey.question'].search([
            ('survey_id', '=', self.survey_2.id),
            ('title', '=', 'Full Question')
        ], limit=1)
        self.assertTrue(duplicated_question)
        self.assertTrue(duplicated_question.is_time_limited)
        self.assertEqual(duplicated_question.time_limit, 45)
        self.assertEqual(duplicated_question.question_placeholder, 'Placeholder text')
        self.assertTrue(duplicated_question.comments_allowed)
        self.assertTrue(duplicated_question.constr_mandatory)
        self.assertEqual(duplicated_question.constr_error_msg, 'Error message')
        self.assertTrue(duplicated_question.validation_required)
        self.assertEqual(duplicated_question.validation_length_min, 2)
        self.assertEqual(duplicated_question.validation_length_max, 20)
        self.assertTrue(duplicated_question.validation_email)
        self.assertTrue(duplicated_question.save_as_email)
        self.assertEqual(duplicated_question.comments_message, 'Add a comment')
        self.assertTrue(duplicated_question.comment_count_as_answer)
        self.assertEqual(duplicated_question.scale_min, 1)
        self.assertEqual(duplicated_question.scale_max, 5)
        self.assertEqual(duplicated_question.scale_min_label, 'Low')
        self.assertEqual(duplicated_question.scale_max_label, 'High')
        duplicated_matrix = self.env['survey.question'].search([
            ('survey_id', '=', self.survey_2.id),
            ('title', '=', 'Matrix Question'),
        ], limit=1)
        self.assertEqual(duplicated_matrix.matrix_subtype, 'multiple')
        self.assertEqual(duplicated_matrix.matrix_row_ids.mapped('value'),
                         ['Row 1'])
        self.assertEqual(duplicated_matrix.suggested_answer_ids.mapped('value'),
                         ['Column 1'])
        self.assertEqual(duplicated_question.validation_error_msg,
                         'Please enter a valid response')

    def test_create_question_remaps_conditional_answers(self):
        """Conditions must point to answers in the destination survey."""
        dependent_question = self.env['survey.question'].create({
            'survey_id': self.survey_1.id,
            'title': 'Conditional Question',
            'question_type': 'text_box',
            'triggering_answer_ids': [Command.set([self.answer_1.id])],
        })
        wizard = self.env['question.duplicate'].create({
            'survey_ids': [Command.set([self.survey_2.id])],
        })
        wizard.with_context(active_ids=[
            self.question_1.id, dependent_question.id,
        ]).action_check_survey()

        copied_trigger_question = self.env['survey.question'].search([
            ('survey_id', '=', self.survey_2.id),
            ('title', '=', 'Test Question 1'),
        ], limit=1)
        copied_dependent_question = self.env['survey.question'].search([
            ('survey_id', '=', self.survey_2.id),
            ('title', '=', 'Conditional Question'),
        ], limit=1)
        self.assertTrue(copied_dependent_question.triggering_answer_ids)
        self.assertEqual(
            copied_dependent_question.triggering_answer_ids.question_id,
            copied_trigger_question,
        )
        self.assertEqual(
            copied_dependent_question.triggering_answer_ids.mapped('value'),
            ['Option 1'],
        )

    def test_action_check_survey_success(self):
        """Test successful question duplication through action_check_survey"""
        wizard = self.env['question.duplicate'].create({
            'survey_ids': [Command.set([self.survey_2.id])],
        })
        # Should not raise any exception
        wizard.with_context(active_ids=[self.question_1.id]).action_check_survey()
        
        # Verify question was created
        duplicated_question = self.env['survey.question'].search([
            ('survey_id', '=', self.survey_2.id),
            ('title', '=', 'Test Question 1')
        ], limit=1)
        self.assertTrue(duplicated_question)

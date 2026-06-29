# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMedicalQuestions(TransactionCase):
    """Test cases for medical.questions model"""

    @classmethod
    def setUpClass(cls):
        super(TestMedicalQuestions, cls).setUpClass()
        cls.question = cls.env['medical.questions'].create({
            'question': 'Do you have any allergies?',
        })

    def test_create(self):
        """Test create() also creates a corresponding medical.questionnaire entry."""
        questionnaire = self.env['medical.questionnaire'].search([
            ('question_id', '=', self.question.id)
        ])
        self.assertTrue(questionnaire.exists(),
                        "A medical.questionnaire entry should be created for every new question.")

    def test_unlink(self):
        """Test unlink() removes both the question and its questionnaire entries."""
        question = self.env['medical.questions'].create({
            'question': 'Do you smoke?',
        })
        question_id = question.id
        question.unlink()
        self.assertFalse(
            self.env['medical.questions'].browse(question_id).exists(),
            "Question record should be deleted."
        )
        self.assertFalse(
            self.env['medical.questionnaire'].search([('question_id', '=', question_id)]).exists(),
            "Questionnaire entries linked to the deleted question should also be removed."
        )

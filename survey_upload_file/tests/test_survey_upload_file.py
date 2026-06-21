# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import json
import base64
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError



class TestSurveyUploadFile(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test survey
        cls.survey = cls.env['survey.survey'].create({
            'title': 'Test Survey for File Upload',
            'users_can_go_back': False,
        })

        # Create questions
        cls.question_upload = cls.env['survey.question'].create({
            'survey_id': cls.survey.id,
            'title': 'Upload your resume',
            'question_type': 'upload_file',
            'upload_multiple_file': False,
        })

        cls.question_upload_mandatory = cls.env['survey.question'].create({
            'survey_id': cls.survey.id,
            'title': 'Upload your ID (Mandatory)',
            'question_type': 'upload_file',
            'constr_mandatory': True,
            'constr_error_msg': 'Please upload your ID.',
        })

        cls.question_char = cls.env['survey.question'].create({
            'survey_id': cls.survey.id,
            'title': 'What is your name?',
            'question_type': 'char_box',
        })

        # Create a user input (survey response session)
        cls.user_input = cls.env['survey.user_input'].create({
            'survey_id': cls.survey.id,
        })

        # Mock file data
        cls.dummy_file_data_1 = base64.b64encode(b'dummy content 1').decode('utf-8')
        cls.dummy_file_data_2 = base64.b64encode(b'dummy content 2').decode('utf-8')

    def test_validate_question_upload_file(self):
        """Test the validate_question method for upload_file type questions."""
        # 1. Non-upload question should delegate to super
        res = self.question_char.validate_question('John Doe')
        self.assertEqual(res, {})

        # 2. Mandatory upload question with empty answer (list format)
        res = self.question_upload_mandatory.validate_question([])
        self.assertIn(self.question_upload_mandatory.id, res)
        self.assertEqual(res[self.question_upload_mandatory.id], 'Please upload your ID.')

        # 3. Mandatory upload question with empty answer (tuple format)
        res = self.question_upload_mandatory.validate_question(([], []))
        self.assertIn(self.question_upload_mandatory.id, res)

        # 4. Mandatory upload question with JSON strings representing empty answers
        res = self.question_upload_mandatory.validate_question((json.dumps([]), json.dumps([])))
        self.assertIn(self.question_upload_mandatory.id, res)

        # 5. Mandatory upload question with invalid JSON strings
        res = self.question_upload_mandatory.validate_question(('invalid_json', 'invalid_json'))
        self.assertIn(self.question_upload_mandatory.id, res)

        # 6. Non-mandatory upload question with empty answer should pass
        res = self.question_upload.validate_question([])
        self.assertEqual(res, {})

        # 7. Mandatory upload question when users CAN go back should pass (no validation error)
        self.survey.users_can_go_back = True
        res = self.question_upload_mandatory.validate_question([])
        self.assertEqual(res, {})
        self.survey.users_can_go_back = False  # Reset

        # 8. Valid answers should pass validation (list/tuple format)
        answer = ([self.dummy_file_data_1], ['resume.pdf'])
        res = self.question_upload_mandatory.validate_question(answer)
        self.assertEqual(res, {})

        # 9. Valid answers should pass validation (JSON strings format)
        answer_json = (json.dumps([self.dummy_file_data_1]), json.dumps(['resume.pdf']))
        res = self.question_upload_mandatory.validate_question(answer_json)
        self.assertEqual(res, {})

    def test_save_lines_upload_file_successful(self):
        """Test successful saving of file upload answers."""
        answer = ([self.dummy_file_data_1, self.dummy_file_data_2], ['file1.txt', 'file2.txt'])
        
        # Save lines for the question
        line = self.user_input._save_lines(self.question_upload, answer)
        
        # Verify the line was created
        self.assertTrue(line)
        self.assertEqual(line.answer_type, 'upload_file')
        self.assertFalse(line.skipped)
        
        # Verify attachments were created and linked correctly
        attachments = line.value_file_data_ids
        self.assertEqual(len(attachments), 2)
        
        # Verify names and data
        self.assertEqual(attachments[0].name, 'file1.txt')
        self.assertEqual(base64.b64decode(attachments[0].datas), b'dummy content 1')
        self.assertEqual(attachments[0].res_model, 'survey.user_input.line')
        self.assertEqual(attachments[0].res_id, line.id)
        self.assertTrue(attachments[0].public)

        self.assertEqual(attachments[1].name, 'file2.txt')
        self.assertEqual(base64.b64decode(attachments[1].datas), b'dummy content 2')
        self.assertEqual(attachments[1].res_model, 'survey.user_input.line')
        self.assertEqual(attachments[1].res_id, line.id)
        self.assertTrue(attachments[1].public)

    def test_save_lines_upload_file_skipped(self):
        """Test saving file upload questions when skipped (no answer provided)."""
        # Save empty answer (None)
        line = self.user_input._save_lines(self.question_upload, None)
        self.assertTrue(line)
        self.assertTrue(line.skipped)
        self.assertFalse(line.answer_type)
        self.assertEqual(len(line.value_file_data_ids), 0)

        # Save empty list/tuple
        line2 = self.user_input._save_lines(self.question_upload, ([], []))
        self.assertEqual(line2.id, line.id)  # Should overwrite/reuse the same line record
        self.assertTrue(line2.skipped)
        self.assertFalse(line2.answer_type)

    def test_save_lines_upload_file_json_format(self):
        """Test saving file upload answers encoded as JSON strings."""
        answer = (json.dumps([self.dummy_file_data_1]), json.dumps(['json_file.pdf']))
        
        line = self.user_input._save_lines(self.question_upload, answer)
        self.assertTrue(line)
        self.assertEqual(line.answer_type, 'upload_file')
        self.assertFalse(line.skipped)
        self.assertEqual(len(line.value_file_data_ids), 1)
        self.assertEqual(line.value_file_data_ids[0].name, 'json_file.pdf')
        self.assertEqual(base64.b64decode(line.value_file_data_ids[0].datas), b'dummy content 1')

    def test_save_lines_overwrite_behavior(self):
        """Test overwrite behavior when saving answer line multiple times."""
        answer1 = ([self.dummy_file_data_1], ['file_first.txt'])
        answer2 = ([self.dummy_file_data_2], ['file_second.txt'])

        # First save
        line = self.user_input._save_lines(self.question_upload, answer1)
        self.assertEqual(len(line.value_file_data_ids), 1)
        self.assertEqual(line.value_file_data_ids[0].name, 'file_first.txt')

        # Should raise when overwrite_existing=False
        with self.assertRaises(UserError):
            self.user_input._save_lines(
                self.question_upload,
                answer2,
                overwrite_existing=False
            )

        # Verify original answer remains unchanged
        self.assertEqual(len(line.value_file_data_ids), 1)
        self.assertEqual(line.value_file_data_ids[0].name, 'file_first.txt')

        # Should overwrite when overwrite_existing=True
        line_overwrite = self.user_input._save_lines(
            self.question_upload,
            answer2,
            overwrite_existing=True
        )

        self.assertEqual(line_overwrite.id, line.id)
        self.assertEqual(len(line_overwrite.value_file_data_ids), 1)
        self.assertEqual(line_overwrite.value_file_data_ids[0].name, 'file_second.txt')

    def test_user_input_line_constraints(self):
        """Test constraints implemented on survey.user_input.line."""
        attachment = self.env['ir.attachment'].create({
            'name': 'test.txt',
            'type': 'binary',
            'datas': self.dummy_file_data_1,
        })

        # 1. Cannot be both skipped and upload_file type
        with self.assertRaises(ValidationError):
            self.env['survey.user_input.line'].create({
                'user_input_id': self.user_input.id,
                'question_id': self.question_upload.id,
                'answer_type': 'upload_file',
                'skipped': True,
                'value_file_data_ids': [(6, 0, [attachment.id])],
            })

        # 2. Cannot have answer_type = 'upload_file' without any attachments
        with self.assertRaises(ValidationError):
            self.env['survey.user_input.line'].create({
                'user_input_id': self.user_input.id,
                'question_id': self.question_upload.id,
                'answer_type': 'upload_file',
                'skipped': False,
                'value_file_data_ids': [(6, 0, [])],
            })

    def test_user_input_line_display_name(self):
        """Test the computed display_name for upload_file survey answer lines."""
        attachment1 = self.env['ir.attachment'].create({
            'name': 'doc1.pdf',
            'type': 'binary',
            'datas': self.dummy_file_data_1,
        })
        attachment2 = self.env['ir.attachment'].create({
            'name': 'doc2.png',
            'type': 'binary',
            'datas': self.dummy_file_data_2,
        })

        line = self.env['survey.user_input.line'].create({
            'user_input_id': self.user_input.id,
            'question_id': self.question_upload.id,
            'answer_type': 'upload_file',
            'value_file_data_ids': [(6, 0, [attachment1.id, attachment2.id])],
        })

        # The display_name should combine the names of the attachments, comma separated
        self.assertEqual(line.display_name, 'doc1.pdf, doc2.png')

    def test_user_input_line_matching_domain(self):
        """Test the _get_answer_matching_domain method for upload_file answer lines."""
        attachment = self.env['ir.attachment'].create({
            'name': 'matching.txt',
            'type': 'binary',
            'datas': self.dummy_file_data_1,
        })

        line = self.env['survey.user_input.line'].create({
            'user_input_id': self.user_input.id,
            'question_id': self.question_upload.id,
            'answer_type': 'upload_file',
            'value_file_data_ids': [(6, 0, [attachment.id])],
        })

        domain = line._get_answer_matching_domain()
        self.assertEqual(domain, [
            '&',
            ('question_id', '=', self.question_upload.id),
            ('value_file_data_ids', 'in', [attachment.id])
        ])

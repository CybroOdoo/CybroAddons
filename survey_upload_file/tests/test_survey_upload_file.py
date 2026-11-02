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

        cls.question_upload_multiple = cls.env['survey.question'].create({
            'survey_id': cls.survey.id,
            'title': 'Upload documents (Multiple)',
            'question_type': 'upload_file',
            'upload_multiple_file': True,
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

    def test_validate_question_incomplete_file_answers(self):
        """A mandatory upload requires both file data and file names."""
        incomplete_answers = [
            ([self.dummy_file_data_1], []),
            ([], ['resume.pdf']),
            ('[]', '["resume.pdf"]'),
            ('["file-data"]', '[]'),
        ]
        for answer in incomplete_answers:
            with self.subTest(answer=answer):
                result = self.question_upload_mandatory.validate_question(answer)
                self.assertEqual(
                    result,
                    {self.question_upload_mandatory.id: 'Please upload your ID.'},
                )

    def test_non_upload_question_save_delegates_to_survey(self):
        """Saving a standard question should keep the base survey behavior."""
        self.user_input._save_lines(self.question_char, 'John Doe')
        line = self.user_input.user_input_line_ids.filtered(
            lambda l: l.question_id == self.question_char
        )

        self.assertEqual(line.question_id, self.question_char)
        self.assertEqual(line.answer_type, 'char_box')
        self.assertEqual(line.value_char_box, 'John Doe')

    def test_non_upload_answer_matching_domain_delegates_to_survey(self):
        """Standard survey answers retain the base matching domain."""
        line = self.env['survey.user_input.line'].create({
            'user_input_id': self.user_input.id,
            'question_id': self.question_char.id,
            'answer_type': 'char_box',
            'value_char_box': 'John Doe',
        })

        self.assertEqual(
            line._get_answer_matching_domain(),
            ['&',
             ('question_id', '=', self.question_char.id),
             ('value_char_box', 'ilike', 'John Doe')],
        )

    def test_save_lines_upload_file_incomplete_answer_is_skipped(self):
        """Partial payloads must not create an upload answer or orphan files."""
        before_count = self.env['ir.attachment'].search_count([
            ('res_model', '=', 'survey.user_input.line'),
        ])

        line = self.user_input._save_lines(
            self.question_upload,
            ([self.dummy_file_data_1], []),
        )

        self.assertTrue(line.skipped)
        self.assertFalse(line.answer_type)
        self.assertFalse(line.value_file_data_ids)
        self.assertEqual(
            self.env['ir.attachment'].search_count([
                ('res_model', '=', 'survey.user_input.line'),
            ]),
            before_count,
        )

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
        
        # Verify names, raw data and file size
        self.assertEqual(attachments[0].name, 'file1.txt')
        self.assertEqual(bytes(attachments[0].raw), b'dummy content 1')
        self.assertEqual(attachments[0].file_size, len(b'dummy content 1'))
        self.assertEqual(attachments[0].res_model, 'survey.user_input.line')
        self.assertEqual(attachments[0].res_id, line.id)
        self.assertTrue(attachments[0].public)

        self.assertEqual(attachments[1].name, 'file2.txt')
        self.assertEqual(bytes(attachments[1].raw), b'dummy content 2')
        self.assertEqual(attachments[1].file_size, len(b'dummy content 2'))
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
        self.assertEqual(bytes(line.value_file_data_ids[0].raw), b'dummy content 1')
        self.assertEqual(line.value_file_data_ids[0].file_size, len(b'dummy content 1'))

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
            'raw': self.dummy_file_data_1,
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
            'raw': self.dummy_file_data_1,
        })
        attachment2 = self.env['ir.attachment'].create({
            'name': 'doc2.png',
            'type': 'binary',
            'raw': self.dummy_file_data_2,
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
            'raw': self.dummy_file_data_1,
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

    def test_attachment_file_size_not_zero(self):
        """Ensure created attachments have proper file_size greater than 0."""
        content = b'Testing file content with non-zero size.'
        b64_content = base64.b64encode(content).decode('utf-8')
        line = self.user_input._save_lines(
            self.question_upload,
            ([b64_content], ['test_size.txt'])
        )
        self.assertEqual(len(line.value_file_data_ids), 1)
        attachment = line.value_file_data_ids[0]
        self.assertGreater(attachment.file_size, 0)
        self.assertEqual(attachment.file_size, len(content))
        self.assertEqual(bytes(attachment.raw), content)

    def test_upload_multiple_files_goback_and_add_another(self):
        """
        When user uploads 1 file, goes back, and uploads another file on a multiple-file question,
        both files must be preserved and present in review answers.
        """
        # Step 1: Upload first file
        answer1 = ([self.dummy_file_data_1], ['file1.txt'], '')
        line = self.user_input._save_lines(self.question_upload_multiple, answer1)
        self.assertEqual(len(line.value_file_data_ids), 1)
        att1 = line.value_file_data_ids[0]
        self.assertEqual(att1.name, 'file1.txt')
        self.assertGreater(att1.file_size, 0)

        # Step 2: User goes back and uploads second file, keeping first file
        answer2 = ([self.dummy_file_data_2], ['file2.txt'], str(att1.id))
        line_updated = self.user_input._save_lines(self.question_upload_multiple, answer2)
        self.assertEqual(line_updated.id, line.id)
        self.assertEqual(len(line_updated.value_file_data_ids), 2)
        names = line_updated.value_file_data_ids.mapped('name')
        self.assertIn('file1.txt', names)
        self.assertIn('file2.txt', names)
        for att in line_updated.value_file_data_ids:
            self.assertGreater(att.file_size, 0)

    def test_goback_without_new_file_preserves_attachments(self):
        """Going back and submitting without re-selecting files preserves existing attachments."""
        # Initial save of 2 files
        answer = ([self.dummy_file_data_1, self.dummy_file_data_2], ['f1.txt', 'f2.txt'], '')
        line = self.user_input._save_lines(self.question_upload_multiple, answer)
        self.assertEqual(len(line.value_file_data_ids), 2)
        existing_ids = ','.join(str(i) for i in line.value_file_data_ids.ids)

        # User goes back, clicks next without changes
        answer_back = ([], [], existing_ids)
        res_validation = self.question_upload_mandatory.validate_question(answer_back)
        self.assertEqual(res_validation, {}, "Mandatory question with existing attachments must pass validation")

        line_after = self.user_input._save_lines(self.question_upload_multiple, answer_back)
        self.assertFalse(line_after.skipped)
        self.assertEqual(len(line_after.value_file_data_ids), 2)

    def test_goback_and_delete_specific_attachment(self):
        """Deleting an existing attachment removes it and preserves the remaining ones."""
        answer = ([self.dummy_file_data_1, self.dummy_file_data_2], ['kept.txt', 'removed.txt'], '')
        line = self.user_input._save_lines(self.question_upload_multiple, answer)
        self.assertEqual(len(line.value_file_data_ids), 2)
        kept_att = line.value_file_data_ids.filtered(lambda a: a.name == 'kept.txt')
        removed_att = line.value_file_data_ids.filtered(lambda a: a.name == 'removed.txt')
        removed_id = removed_att.id

        # User goes back and deletes removed.txt, keeping only kept.txt
        answer_delete = ([], [], str(kept_att.id))
        line_after = self.user_input._save_lines(self.question_upload_multiple, answer_delete)
        self.assertEqual(len(line_after.value_file_data_ids), 1)
        self.assertEqual(line_after.value_file_data_ids[0].name, 'kept.txt')
        # Verify removed attachment was unlinked from DB
        self.assertFalse(self.env['ir.attachment'].browse(removed_id).exists())

    def test_single_file_upload_replaces_on_new_file(self):
        """For single-file upload question, uploading a new file replaces the old one."""
        answer1 = ([self.dummy_file_data_1], ['old.txt'], '')
        line = self.user_input._save_lines(self.question_upload, answer1)
        old_att_id = line.value_file_data_ids[0].id

        answer2 = ([self.dummy_file_data_2], ['new.txt'], str(old_att_id))
        line_updated = self.user_input._save_lines(self.question_upload, answer2)
        self.assertEqual(len(line_updated.value_file_data_ids), 1)
        self.assertEqual(line_updated.value_file_data_ids[0].name, 'new.txt')
        self.assertFalse(self.env['ir.attachment'].browse(old_att_id).exists())

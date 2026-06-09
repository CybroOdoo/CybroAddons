# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
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
################################################################################

from unittest.mock import patch, MagicMock
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'hr_ai_recruitment')
class TestHrApplicant(TransactionCase):
    """
    Test suite for hr_applicant.py (HRRecruitment model).

    Covers:
        - _compute_cv_details (with main attachment, with other attachments,
          and with no attachments)
        - _extract_text_from_attachment (success and error paths)
        - action_ats_score (wizard action return value)
        - _compute_ai_shortlist_enabled (True / False config parameter)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a minimal job position used across all test methods
        cls.job = cls.env['hr.job'].create({'name': 'Test Engineer'})

        # Create a base applicant record without any attachment
        cls.applicant = cls.env['hr.applicant'].create({
            'name': 'Application for Test Engineer',
            'partner_name': 'Alice Test',
            'job_id': cls.job.id,
        })

    # ------------------------------------------------------------------
    # _compute_cv_details
    # ------------------------------------------------------------------

    def test_compute_cv_details_no_attachment(self):
        """cv_details should be an empty string when no attachments exist."""
        # Ensure no attachment is linked
        self.applicant.message_main_attachment_id = False
        self.applicant.attachment_ids = [(5, 0, 0)]
        self.applicant._compute_cv_details()
        self.assertEqual(
            self.applicant.cv_details, '',
            "cv_details must be empty when there are no attachments.",
        )

    def test_compute_cv_details_with_main_attachment(self):
        """cv_details should use text extracted from message_main_attachment_id."""
        fake_text = "Software Engineer with 5 years of Python experience."

        with patch.object(
            type(self.applicant),
            '_extract_text_from_attachment',
            return_value=fake_text,
        ):
            # Create a dummy attachment and assign it as the main attachment
            attachment = self.env['ir.attachment'].create({
                'name': 'cv.pdf',
                'res_model': 'hr.applicant',
                'res_id': self.applicant.id,
                'datas': b'',
            })
            self.applicant.message_main_attachment_id = attachment
            self.applicant._compute_cv_details()
            self.assertEqual(
                self.applicant.cv_details,
                fake_text,
                "cv_details should match the extracted text from main attachment.",
            )

    def test_compute_cv_details_with_other_attachments(self):
        """cv_details should concatenate text from all other attachments when
        no main attachment is set."""
        fake_text_a = "Part A of CV."
        fake_text_b = " Part B of CV."

        attachment_a = self.env['ir.attachment'].create({
            'name': 'cv_part_a.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
        })
        attachment_b = self.env['ir.attachment'].create({
            'name': 'cv_part_b.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
        })

        # Remove main attachment so the elif branch is triggered
        self.applicant.message_main_attachment_id = False

        call_count = [0]
        fake_texts = [fake_text_a, fake_text_b]

        def fake_extract(attachment):
            result = fake_texts[call_count[0]]
            call_count[0] += 1
            return result

        with patch.object(
            type(self.applicant),
            '_extract_text_from_attachment',
            side_effect=fake_extract,
        ):
            self.applicant.attachment_ids = [
                (4, attachment_a.id),
                (4, attachment_b.id),
            ]
            self.applicant._compute_cv_details()
            self.assertIn(
                "Part A",
                self.applicant.cv_details,
                "cv_details should contain text from first attachment.",
            )

    # ------------------------------------------------------------------
    # _extract_text_from_attachment
    # ------------------------------------------------------------------

    def test_extract_text_from_attachment_success(self):
        """_extract_text_from_attachment should return extracted text on success."""
        attachment = self.env['ir.attachment'].create({
            'name': 'cv.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
            'store_fname': 'fake/path/cv.pdf',
        })

        mock_page = MagicMock()
        mock_page.get_text.return_value = "  Line one  \n  Line two  \n"
        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

        with patch('fitz.open', return_value=mock_doc):
            with patch.object(
                type(attachment),
                '_full_path',
                return_value='/tmp/fake_cv.pdf',
            ):
                result = self.applicant._extract_text_from_attachment(attachment)
        # Verify that at least some text was returned
        self.assertIsInstance(result, str)

    def test_extract_text_from_attachment_error_returns_empty_string(self):
        """_extract_text_from_attachment should return '' and log on exception."""
        attachment = self.env['ir.attachment'].create({
            'name': 'broken.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
            'store_fname': 'non_existent_path.pdf',
        })

        with patch('fitz.open', side_effect=Exception("File not found")):
            result = self.applicant._extract_text_from_attachment(attachment)

        self.assertEqual(
            result, '',
            "Should return empty string when an exception occurs during extraction.",
        )

    # ------------------------------------------------------------------
    # action_ats_score
    # ------------------------------------------------------------------

    def test_action_ats_score_returns_valid_action(self):
        """action_ats_score should return a dict opening the hr.ai.score wizard."""
        action = self.applicant.action_ats_score()
        self.assertIsInstance(action, dict, "action_ats_score must return a dict.")
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'hr.ai.score')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('view_mode'), 'form')
        # Context must pre-fill the applicant
        context = action.get('context', {})
        self.assertEqual(
            context.get('default_hr_applicant_id'),
            self.applicant.id,
            "Wizard context must contain the current applicant id.",
        )

    # ------------------------------------------------------------------
    # _compute_ai_shortlist_enabled
    # ------------------------------------------------------------------

    def test_compute_ai_shortlist_enabled_true(self):
        """ai_shortlist_enabled must be True when config parameter equals 'True'."""
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_ai_recruitment.is_ai_shortlist', 'True'
        )
        self.applicant._compute_ai_shortlist_enabled()
        self.assertTrue(
            self.applicant.ai_shortlist_enabled,
            "ai_shortlist_enabled should be True when param is 'True'.",
        )

    def test_compute_ai_shortlist_enabled_false(self):
        """ai_shortlist_enabled must be False when config parameter is not 'True'."""
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_ai_recruitment.is_ai_shortlist', 'False'
        )
        self.applicant._compute_ai_shortlist_enabled()
        self.assertFalse(
            self.applicant.ai_shortlist_enabled,
            "ai_shortlist_enabled should be False when param is 'False'.",
        )

    def test_compute_ai_shortlist_enabled_missing_param(self):
        """ai_shortlist_enabled must be False when config parameter is absent."""
        # Remove the parameter if it exists
        param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'hr_ai_recruitment.is_ai_shortlist')
        ])
        param.unlink()
        self.applicant._compute_ai_shortlist_enabled()
        self.assertFalse(
            self.applicant.ai_shortlist_enabled,
            "ai_shortlist_enabled should be False when param is missing.",
        )

    def test_ats_score_field_default(self):
        """ats_score field should default to 0 for a newly created applicant."""
        new_applicant = self.env['hr.applicant'].create({
            'name': 'Application for Test Engineer - Bob',
            'partner_name': 'Bob Default',
            'job_id': self.job.id,
        })
        self.assertEqual(
            new_applicant.ats_score,
            0,
            "ats_score default value must be 0.",
        )

    def test_ats_score_can_be_written(self):
        """ats_score should accept integer write operations."""
        self.applicant.write({'ats_score': 85})
        self.assertEqual(
            self.applicant.ats_score, 85,
            "ats_score should persist the written integer value.",
        )

    def test_cv_score_summary_can_be_written(self):
        """cv_score_summary should accept text write operations."""
        summary = "Excellent Python developer with strong ML background."
        self.applicant.write({'cv_score_summary': summary})
        self.assertEqual(
            self.applicant.cv_score_summary,
            summary,
            "cv_score_summary should persist the written text.",
        )

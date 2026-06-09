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

from unittest.mock import patch
from odoo.tests import tagged, TransactionCase
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install', 'hr_ai_recruitment')
class TestHrAiScore(TransactionCase):
    """
    Test suite for wizard/hr_ai_score.py (HrAiScore transient model).

    Corresponds to functions:
        - _get_default_shortlist      : reads config param and returns int or False
        - action_calculate_score      : validates inputs, calls OLG API, parses
                                        score, writes to applicant; raises on
                                        missing data, prompt-too-long, API error,
                                        network error, and timeout.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.job = cls.env['hr.job'].create({'name': 'AI Test Engineer'})
        cls.applicant = cls.env['hr.applicant'].create({
            'name': 'Application for AI Test Engineer',
            'partner_name': 'Eve Applicant',
            'job_id': cls.job.id,
        })
        cls.shortlist = cls.env['hr.shortlist'].create({
            'name': 'Default Criteria',
        })
        cls.env['hr.shortlist.line'].create({
            'name': 'Python Skills',
            'score': 50,
            'hr_shortlist_id': cls.shortlist.id,
        })

    def _make_wizard(self, shortlist=None, applicant=None):
        """Helper: create an hr.ai.score wizard with given or default values."""
        return self.env['hr.ai.score'].create({
            'hr_shortlist_id': (shortlist or self.shortlist).id,
            'hr_applicant_id': (applicant or self.applicant).id,
        })

    def test_get_default_shortlist_returns_int_when_param_set(self):
        """
        _get_default_shortlist must return the shortlist id (int)
        when 'hr_ai_recruitment.hr_shortlist' param is set.
        """
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_ai_recruitment.hr_shortlist', str(self.shortlist.id)
        )
        result = self.env['hr.ai.score']._get_default_shortlist()
        self.assertEqual(
            result,
            self.shortlist.id,
            "_get_default_shortlist should return the int id stored in param.",
        )

    def test_get_default_shortlist_returns_false_when_param_absent(self):
        """
        _get_default_shortlist must return False
        when 'hr_ai_recruitment.hr_shortlist' param is not set.
        """
        self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'hr_ai_recruitment.hr_shortlist')
        ]).unlink()
        result = self.env['hr.ai.score']._get_default_shortlist()
        self.assertFalse(
            result,
            "_get_default_shortlist should return False when param is absent.",
        )

    def test_action_calculate_score_raises_when_no_shortlist(self):
        """
        action_calculate_score must raise ValidationError
        when hr_shortlist_id is not set.
        """
        wizard = self.env['hr.ai.score'].create({
            'hr_applicant_id': self.applicant.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_calculate_score()

    def test_action_calculate_score_raises_when_no_attachment(self):
        """
        action_calculate_score must raise ValidationError
        when attachment_id (main CV) is not set.
        """
        # Ensure applicant has no main attachment
        self.applicant.message_main_attachment_id = False
        wizard = self.env['hr.ai.score'].create({
            'hr_shortlist_id': self.shortlist.id,
            'hr_applicant_id': self.applicant.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_calculate_score()

    def test_action_calculate_score_success_updates_applicant(self):
        """
        action_calculate_score must write ats_score and cv_score_summary
        to the applicant when the OLG API returns a successful response
        containing a parseable total_score.
        """
        attachment = self.env['ir.attachment'].create({
            'name': 'cv.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
        })
        self.applicant.message_main_attachment_id = attachment

        mock_response = {
            'status': 'success',
            'content': 'Candidate analysis complete. total_score = 78',
        }

        wizard = self._make_wizard()
        with patch(
            'odoo.addons.iap.tools.iap_tools.iap_jsonrpc',
            return_value=mock_response,
        ):
            result = wizard.action_calculate_score()

        self.assertEqual(
            self.applicant.ats_score,
            78,
            "ats_score must be set to the value extracted from the API response.",
        )
        self.assertIn(
            'total_score',
            self.applicant.cv_score_summary,
            "cv_score_summary must be populated with the API response content.",
        )
        self.assertEqual(
            result.get('type'),
            'ir.actions.act_window_close',
            "action_calculate_score must return act_window_close on success.",
        )

    def test_action_calculate_score_raises_when_score_not_in_response(self):
        """
        action_calculate_score must raise ValidationError when the API returns
        'success' but the response content does not contain 'total_score = <n>'.
        """
        attachment = self.env['ir.attachment'].create({
            'name': 'cv2.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
        })
        self.applicant.message_main_attachment_id = attachment

        mock_response = {
            'status': 'success',
            'content': 'The candidate looks promising.',   # no total_score variable
        }

        wizard = self._make_wizard()
        with patch(
            'odoo.addons.iap.tools.iap_tools.iap_jsonrpc',
            return_value=mock_response,
        ):
            with self.assertRaises(ValidationError):
                wizard.action_calculate_score()

    def test_action_calculate_score_raises_on_prompt_too_long(self):
        """
        action_calculate_score must raise ValidationError
        when the API status is 'error_prompt_too_long'.
        """
        attachment = self.env['ir.attachment'].create({
            'name': 'cv3.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
        })
        self.applicant.message_main_attachment_id = attachment

        mock_response = {'status': 'error_prompt_too_long'}

        wizard = self._make_wizard()
        with patch(
            'odoo.addons.iap.tools.iap_tools.iap_jsonrpc',
            return_value=mock_response,
        ):
            with self.assertRaises(ValidationError):
                wizard.action_calculate_score()

    def test_action_calculate_score_raises_on_generic_api_error(self):
        """
        action_calculate_score must raise ValidationError
        when the API returns any non-success, non-prompt-too-long status.
        """
        attachment = self.env['ir.attachment'].create({
            'name': 'cv4.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
        })
        self.applicant.message_main_attachment_id = attachment

        mock_response = {
            'status': 'error_authentication',
            'message': 'Invalid API key',
        }

        wizard = self._make_wizard()
        with patch(
            'odoo.addons.iap.tools.iap_tools.iap_jsonrpc',
            return_value=mock_response,
        ):
            with self.assertRaises(ValidationError):
                wizard.action_calculate_score()

    def test_action_calculate_score_raises_user_error_on_connection_error(self):
        """
        action_calculate_score must raise UserError
        when a network ConnectionError is caught.
        """
        from requests.exceptions import ConnectionError as ReqConnectionError

        attachment = self.env['ir.attachment'].create({
            'name': 'cv5.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
        })
        self.applicant.message_main_attachment_id = attachment

        wizard = self._make_wizard()
        with patch(
            'odoo.addons.iap.tools.iap_tools.iap_jsonrpc',
            side_effect=ReqConnectionError("Network unreachable"),
        ):
            with self.assertRaises(UserError):
                wizard.action_calculate_score()

    def test_action_calculate_score_raises_user_error_on_timeout(self):
        """
        action_calculate_score must raise UserError
        when a requests Timeout is caught.
        """
        from requests.exceptions import Timeout as ReqTimeout

        attachment = self.env['ir.attachment'].create({
            'name': 'cv6.pdf',
            'res_model': 'hr.applicant',
            'res_id': self.applicant.id,
            'datas': b'',
        })
        self.applicant.message_main_attachment_id = attachment

        wizard = self._make_wizard()
        with patch(
            'odoo.addons.iap.tools.iap_tools.iap_jsonrpc',
            side_effect=ReqTimeout("Request timed out"),
        ):
            with self.assertRaises(UserError):
                wizard.action_calculate_score()

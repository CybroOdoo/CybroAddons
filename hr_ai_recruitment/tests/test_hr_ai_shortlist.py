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

from odoo import fields
from odoo.tests import tagged, TransactionCase
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install', 'hr_ai_recruitment')
class TestHrAiShortlist(TransactionCase):
    """
    Test suite for wizard/hr_ai_shortlist.py (AiShortlistWizard transient model).

    Corresponds to functions:
        - _onchange_stage_id           : auto-populates applicant_ids when
                                         the recruitment stage changes.
        - action_application_shortlist : filters applicants by ATS score /
                                         operator, links shortlisted applicants
                                         to the job, returns a notification action.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.job = cls.env['hr.job'].create({'name': 'Backend Developer'})

        # Recruitment stage
        cls.stage = cls.env['hr.recruitment.stage'].create({
            'name': 'Initial Screening',
            'sequence': 1,
        })

        # Applicants with different ATS scores
        cls.applicant_high = cls.env['hr.applicant'].create({
            'name': 'Application for Backend Developer - Frank',
            'partner_name': 'Frank High',
            'job_id': cls.job.id,
            'stage_id': cls.stage.id,
            'ats_score': 85,
        })
        cls.applicant_mid = cls.env['hr.applicant'].create({
            'name': 'Application for Backend Developer - Grace',
            'partner_name': 'Grace Mid',
            'job_id': cls.job.id,
            'stage_id': cls.stage.id,
            'ats_score': 60,
        })
        cls.applicant_low = cls.env['hr.applicant'].create({
            'name': 'Application for Backend Developer - Henry',
            'partner_name': 'Henry Low',
            'job_id': cls.job.id,
            'stage_id': cls.stage.id,
            'ats_score': 40,
        })

    def _make_wizard(self, operator='>', required_score=50,
                     applicants=None, stage=None, job=None):
        """Helper: create a wizard pre-loaded with test applicants."""
        app_ids = (applicants or
                   (self.applicant_high | self.applicant_mid | self.applicant_low))
        wizard = self.env['hr.ai.shortlist'].create({
            'job_id': (job or self.job).id,
            'stage_id': (stage or self.stage).id,
            'required_score': required_score,
            'operators': operator,
            'applicant_ids': [fields.Command.link(a.id) for a in app_ids],
        })
        return wizard

    # ------------------------------------------------------------------
    # _onchange_stage_id
    # ------------------------------------------------------------------

    def test_onchange_stage_id_populates_applicant_ids(self):
        """
        _onchange_stage_id must load all applicants matching the
        selected stage and job into applicant_ids.
        """
        wizard = self.env['hr.ai.shortlist'].new({
            'job_id': self.job.id,
            'stage_id': self.stage.id,
        })
        wizard._onchange_stage_id()

        loaded_ids = wizard.applicant_ids.ids
        self.assertIn(
            self.applicant_high.id,
            loaded_ids,
            "applicant_high should appear in applicant_ids after onchange.",
        )
        self.assertIn(
            self.applicant_mid.id,
            loaded_ids,
            "applicant_mid should appear in applicant_ids after onchange.",
        )
        self.assertIn(
            self.applicant_low.id,
            loaded_ids,
            "applicant_low should appear in applicant_ids after onchange.",
        )

    def test_onchange_stage_id_excludes_other_job_applicants(self):
        """
        _onchange_stage_id must NOT load applicants from a different job
        even if they share the same stage.
        """
        other_job = self.env['hr.job'].create({'name': 'Frontend Developer'})
        other_applicant = self.env['hr.applicant'].create({
            'name': 'Application for Frontend Developer - Ivan',
            'partner_name': 'Ivan Other',
            'job_id': other_job.id,
            'stage_id': self.stage.id,
            'ats_score': 70,
        })

        wizard = self.env['hr.ai.shortlist'].new({
            'job_id': self.job.id,
            'stage_id': self.stage.id,
        })
        wizard._onchange_stage_id()

        self.assertNotIn(
            other_applicant.id,
            wizard.applicant_ids.ids,
            "Applicants from a different job must not appear after onchange.",
        )

    def test_onchange_stage_id_clears_applicants_when_no_stage(self):
        """
        _onchange_stage_id with stage_id = False should result in an
        empty applicant_ids (no applicants match domain).
        """
        wizard = self.env['hr.ai.shortlist'].new({
            'job_id': self.job.id,
            'stage_id': False,
        })
        wizard._onchange_stage_id()
        self.assertFalse(
            wizard.applicant_ids,
            "applicant_ids should be empty when no stage is selected.",
        )

    # ------------------------------------------------------------------
    # action_application_shortlist — validation
    # ------------------------------------------------------------------

    def test_action_application_shortlist_raises_when_no_operator(self):
        """
        action_application_shortlist must raise ValidationError
        when no operator is selected.
        """
        wizard = self.env['hr.ai.shortlist'].create({
            'job_id': self.job.id,
            'stage_id': self.stage.id,
            'required_score': 50,
            'applicant_ids': [
                fields.Command.link(self.applicant_high.id)
            ],
        })
        with self.assertRaises(ValidationError):
            wizard.action_application_shortlist()

    # ------------------------------------------------------------------
    # action_application_shortlist — operator '>'
    # ------------------------------------------------------------------

    def test_action_application_shortlist_operator_greater_than(self):
        """
        action_application_shortlist with '>' operator must shortlist only
        applicants whose ats_score is strictly greater than required_score.
        """
        wizard = self._make_wizard(operator='>', required_score=60)
        wizard.action_application_shortlist()

        shortlisted = self.job.shortlisted_applicant_ids
        self.assertIn(
            self.applicant_high,
            shortlisted,
            "applicant_high (score=85) must be shortlisted with '>' 60.",
        )
        self.assertNotIn(
            self.applicant_mid,
            shortlisted,
            "applicant_mid (score=60) must NOT be shortlisted with '>' 60.",
        )
        self.assertNotIn(
            self.applicant_low,
            shortlisted,
            "applicant_low (score=40) must NOT be shortlisted with '>' 60.",
        )

    # ------------------------------------------------------------------
    # action_application_shortlist — operator '>='
    # ------------------------------------------------------------------

    def test_action_application_shortlist_operator_greater_equal(self):
        """
        action_application_shortlist with '>=' operator must shortlist
        applicants whose ats_score >= required_score.
        """
        # Reset shortlisted applicants first
        self.job.shortlisted_applicant_ids = [(5, 0, 0)]

        wizard = self._make_wizard(operator='>=', required_score=60)
        wizard.action_application_shortlist()

        shortlisted = self.job.shortlisted_applicant_ids
        self.assertIn(self.applicant_high, shortlisted)
        self.assertIn(self.applicant_mid, shortlisted)
        self.assertNotIn(self.applicant_low, shortlisted)

    # ------------------------------------------------------------------
    # action_application_shortlist — operator '='
    # ------------------------------------------------------------------

    def test_action_application_shortlist_operator_equal(self):
        """
        action_application_shortlist with '=' operator must shortlist only
        applicants whose ats_score exactly equals required_score.
        """
        self.job.shortlisted_applicant_ids = [(5, 0, 0)]

        wizard = self._make_wizard(operator='=', required_score=60)
        wizard.action_application_shortlist()

        shortlisted = self.job.shortlisted_applicant_ids
        self.assertIn(self.applicant_mid, shortlisted)
        self.assertNotIn(self.applicant_high, shortlisted)
        self.assertNotIn(self.applicant_low, shortlisted)

    # ------------------------------------------------------------------
    # action_application_shortlist — operator '<'
    # ------------------------------------------------------------------

    def test_action_application_shortlist_operator_less_than(self):
        """
        action_application_shortlist with '<' operator must shortlist only
        applicants whose ats_score is strictly less than required_score.
        """
        self.job.shortlisted_applicant_ids = [(5, 0, 0)]

        wizard = self._make_wizard(operator='<', required_score=60)
        wizard.action_application_shortlist()

        shortlisted = self.job.shortlisted_applicant_ids
        self.assertIn(self.applicant_low, shortlisted)
        self.assertNotIn(self.applicant_high, shortlisted)
        self.assertNotIn(self.applicant_mid, shortlisted)

    # ------------------------------------------------------------------
    # action_application_shortlist — operator '<='
    # ------------------------------------------------------------------

    def test_action_application_shortlist_operator_less_equal(self):
        """
        action_application_shortlist with '<=' operator must shortlist
        applicants whose ats_score <= required_score.
        """
        self.job.shortlisted_applicant_ids = [(5, 0, 0)]

        wizard = self._make_wizard(operator='<=', required_score=60)
        wizard.action_application_shortlist()

        shortlisted = self.job.shortlisted_applicant_ids
        self.assertIn(self.applicant_mid, shortlisted)
        self.assertIn(self.applicant_low, shortlisted)
        self.assertNotIn(self.applicant_high, shortlisted)

    # ------------------------------------------------------------------
    # action_application_shortlist — applicants without ats_score are skipped
    # ------------------------------------------------------------------

    def test_action_application_shortlist_skips_applicant_with_no_ats_score(self):
        """
        Applicants with ats_score = 0 (falsy) must be counted as skipped,
        not matched against any operator.

        Note: Integer fields default to 0, which evaluates as falsy in Python;
        the production code guards: 'if applicant.ats_score is not None'.
        Since 0 is not None, applicants with score=0 are still evaluated.
        This test documents that behaviour explicitly.
        """
        self.job.shortlisted_applicant_ids = [(5, 0, 0)]

        applicant_zero = self.env['hr.applicant'].create({
            'name': 'Application for Backend Developer - Zara',
            'partner_name': 'Zara Zero',
            'job_id': self.job.id,
            'stage_id': self.stage.id,
            'ats_score': 0,
        })
        wizard = self._make_wizard(
            operator='>=',
            required_score=1,
            applicants=applicant_zero,
        )
        wizard.action_application_shortlist()

        # ats_score=0 is not >= 1, so applicant_zero must NOT be shortlisted
        self.assertNotIn(
            applicant_zero,
            self.job.shortlisted_applicant_ids,
            "Applicant with ats_score=0 must not satisfy '>= 1'.",
        )

    # ------------------------------------------------------------------
    # action_application_shortlist — return value (notification)
    # ------------------------------------------------------------------

    def test_action_application_shortlist_returns_notification_action(self):
        """
        action_application_shortlist must return a dict with type
        'ir.actions.client' and tag 'display_notification'.
        """
        wizard = self._make_wizard(operator='>', required_score=50)
        result = wizard.action_application_shortlist()

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'display_notification')
        params = result.get('params', {})
        self.assertIn('message', params)
        self.assertIn('type', params)

    def test_action_application_shortlist_success_type_when_shortlisted(self):
        """
        When at least one applicant is shortlisted, the notification type
        must be 'success'.
        """
        self.job.shortlisted_applicant_ids = [(5, 0, 0)]
        wizard = self._make_wizard(operator='>', required_score=50)
        result = wizard.action_application_shortlist()
        self.assertEqual(result['params']['type'], 'success')

    def test_action_application_shortlist_warning_type_when_none_shortlisted(self):
        """
        When no applicants meet the filter criteria, the notification type
        must be 'warning'.
        """
        self.job.shortlisted_applicant_ids = [(5, 0, 0)]
        # required_score=200 is impossible for any applicant
        wizard = self._make_wizard(operator='>', required_score=200)
        result = wizard.action_application_shortlist()
        self.assertEqual(result['params']['type'], 'warning')

    def test_action_application_shortlist_links_shortlisted_to_job(self):
        """
        action_application_shortlist must write the filtered applicants
        into job.shortlisted_applicant_ids.
        """
        self.job.shortlisted_applicant_ids = [(5, 0, 0)]
        wizard = self._make_wizard(operator='>=', required_score=85)
        wizard.action_application_shortlist()

        self.assertIn(
            self.applicant_high,
            self.job.shortlisted_applicant_ids,
            "applicant_high must be linked to the job's shortlisted_applicant_ids.",
        )

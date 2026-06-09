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

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'hr_ai_recruitment')
class TestHrJob(TransactionCase):
    """
    Test suite for hr_job.py (HrJob model).

    Covers:
        - action_shortlist (returns correct action dict)
        - _compute_ai_shortlist_enabled (True / False / missing param)
        - shortlisted_applicant_ids Many2many field behaviour
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.job = cls.env['hr.job'].create({'name': 'QA Engineer'})

    # ------------------------------------------------------------------
    # _compute_ai_shortlist_enabled
    # ------------------------------------------------------------------

    def test_compute_ai_shortlist_enabled_true(self):
        """ai_shortlist_enabled must be True when param equals 'True'."""
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_ai_recruitment.is_ai_shortlist', 'True'
        )
        self.job._compute_ai_shortlist_enabled()
        self.assertTrue(
            self.job.ai_shortlist_enabled,
            "ai_shortlist_enabled should be True when param is 'True'.",
        )

    def test_compute_ai_shortlist_enabled_false(self):
        """ai_shortlist_enabled must be False when param equals 'False'."""
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_ai_recruitment.is_ai_shortlist', 'False'
        )
        self.job._compute_ai_shortlist_enabled()
        self.assertFalse(
            self.job.ai_shortlist_enabled,
            "ai_shortlist_enabled should be False when param is 'False'.",
        )

    def test_compute_ai_shortlist_enabled_missing_param(self):
        """ai_shortlist_enabled must be False when config parameter is absent."""
        param = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'hr_ai_recruitment.is_ai_shortlist')
        ])
        param.unlink()
        self.job._compute_ai_shortlist_enabled()
        self.assertFalse(
            self.job.ai_shortlist_enabled,
            "ai_shortlist_enabled should be False when param is missing.",
        )

    def test_compute_ai_shortlist_enabled_multiple_jobs(self):
        """The same param value should apply uniformly across multiple job records."""
        job2 = self.env['hr.job'].create({'name': 'DevOps Engineer'})
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_ai_recruitment.is_ai_shortlist', 'True'
        )
        jobs = self.job | job2
        jobs._compute_ai_shortlist_enabled()
        for job in jobs:
            self.assertTrue(
                job.ai_shortlist_enabled,
                f"ai_shortlist_enabled should be True for job '{job.name}'.",
            )

    # ------------------------------------------------------------------
    # action_shortlist
    # ------------------------------------------------------------------

    def test_action_shortlist_returns_dict(self):
        """action_shortlist must return a dict."""
        action = self.job.action_shortlist()
        self.assertIsInstance(action, dict, "action_shortlist must return a dict.")

    def test_action_shortlist_opens_correct_model(self):
        """action_shortlist must open the hr.ai.shortlist wizard."""
        action = self.job.action_shortlist()
        self.assertEqual(
            action.get('res_model'),
            'hr.ai.shortlist',
            "action_shortlist should open hr.ai.shortlist model.",
        )

    def test_action_shortlist_target_new(self):
        """action_shortlist must open the wizard as a popup (target='new')."""
        action = self.job.action_shortlist()
        self.assertEqual(
            action.get('target'),
            'new',
            "action_shortlist should open in a popup window.",
        )

    def test_action_shortlist_context_contains_job_id(self):
        """action_shortlist context must pre-fill default_job_id with current job."""
        action = self.job.action_shortlist()
        context = action.get('context', {})
        self.assertEqual(
            context.get('default_job_id'),
            self.job.id,
            "Wizard context must contain the current job id.",
        )

    def test_action_shortlist_action_type(self):
        """action_shortlist must return an ir.actions.act_window type."""
        action = self.job.action_shortlist()
        self.assertEqual(
            action.get('type'),
            'ir.actions.act_window',
            "Action type must be 'ir.actions.act_window'.",
        )

    # ------------------------------------------------------------------
    # shortlisted_applicant_ids field
    # ------------------------------------------------------------------

    def test_shortlisted_applicant_ids_initially_empty(self):
        """A freshly created job should have no shortlisted applicants."""
        new_job = self.env['hr.job'].create({'name': 'Data Scientist'})
        self.assertFalse(
            new_job.shortlisted_applicant_ids,
            "shortlisted_applicant_ids should be empty by default.",
        )

    def test_shortlisted_applicant_ids_can_be_linked(self):
        """Applicants can be linked to a job's shortlisted_applicant_ids."""
        applicant = self.env['hr.applicant'].create({
            'name': 'Application for QA Engineer - Charlie',
            'partner_name': 'Charlie Shortlist',
            'job_id': self.job.id,
        })
        self.job.write({
            'shortlisted_applicant_ids': [(4, applicant.id)]
        })
        self.assertIn(
            applicant,
            self.job.shortlisted_applicant_ids,
            "Applicant should appear in shortlisted_applicant_ids after linking.",
        )

    def test_shortlisted_applicant_ids_can_be_unlinked(self):
        """Applicants can be removed from a job's shortlisted_applicant_ids."""
        applicant = self.env['hr.applicant'].create({
            'name': 'Application for QA Engineer - Dave',
            'partner_name': 'Dave Unlink',
            'job_id': self.job.id,
        })
        self.job.write({'shortlisted_applicant_ids': [(4, applicant.id)]})
        self.job.write({'shortlisted_applicant_ids': [(3, applicant.id)]})
        self.assertNotIn(
            applicant,
            self.job.shortlisted_applicant_ids,
            "Applicant should be removed from shortlisted_applicant_ids after unlinking.",
        )

# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
# pylint: disable=protected-access
"""Unit test suite for schedule_survey module."""
from datetime import timedelta
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'schedule_survey')
class TestSurveyScheduler(TransactionCase):
    """Test suite for survey scheduling and automated email distribution."""

    @classmethod
    def setUpClass(cls):
        """Prepare survey and partner records for test execution."""
        super().setUpClass()
        if not cls.env.user.email:
            cls.env.user.email = 'admin@cybrosys.com'

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Survey Participant',
            'email': 'participant@gmail.com',
        })

        cls.survey = cls.env['survey.survey'].create({
            'title': 'Scheduled Customer Feedback Survey',
            'is_cron': True,
            'scheduled_date': fields.Date.today(),
            'cron_status': 'in_progress',
            'contact_ids': [(4, cls.partner.id)],
        })

    def test_survey_schedule_fields(self):
        """Verify survey scheduling fields defaults and assignment."""
        self.assertTrue(self.survey.is_cron)
        self.assertEqual(self.survey.scheduled_date, fields.Date.today())
        self.assertEqual(self.survey.cron_status, 'in_progress')
        self.assertIn(self.partner, self.survey.contact_ids)

    def test_onchange_scheduled_date(self):
        """Verify onchange sets cron_status to in_progress for valid dates."""
        new_survey = self.env['survey.survey'].new({
            'title': 'Onchange Test Survey',
            'scheduled_date': fields.Date.today() + timedelta(days=2),
        })
        new_survey._onchange_scheduled_date()
        self.assertEqual(new_survey.cron_status, 'in_progress')

    def test_send_scheduled_survey_cron(self):
        """Verify send_scheduled_survey processes scheduled survey."""
        self.env['survey.survey'].send_scheduled_survey()
        self.assertEqual(self.survey.cron_status, 'done')

    def test_send_scheduled_survey_filters(self):
        """Verify cron ignores disabled, future, or completed surveys."""
        disabled_survey = self.env['survey.survey'].create({
            'title': 'Disabled Cron Survey',
            'is_cron': False,
            'scheduled_date': fields.Date.today(),
            'cron_status': 'in_progress',
            'contact_ids': [(4, self.partner.id)],
        })
        future_survey = self.env['survey.survey'].create({
            'title': 'Future Scheduled Survey',
            'is_cron': True,
            'scheduled_date': fields.Date.today() + timedelta(days=7),
            'cron_status': 'in_progress',
            'contact_ids': [(4, self.partner.id)],
        })

        self.env['survey.survey'].send_scheduled_survey()
        self.assertEqual(disabled_survey.cron_status, 'in_progress')
        self.assertEqual(future_survey.cron_status, 'in_progress')

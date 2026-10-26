# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import date

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import PharmaRetentionCommon


@tagged('post_install', '-at_install')
class TestRetentionSample(PharmaRetentionCommon):
    """Creating, confirming and protecting reserve samples."""

    def test_create_from_released_lot(self):
        """The draft sample takes its rule, location and QA release from the batch."""
        lot = self.released_lot()
        production = self.env['mrp.production'].create({'product_id': self.product.id})
        release = self.env['pharma.qa.release'].create({
            'production_id': production.id, 'lot_id': lot.id,
        })
        self.assertTrue(lot.show_retain_sample)
        self.assertTrue(release.show_retain_sample)
        release.with_user(self.operator).action_create_retention_sample()
        sample = lot.retention_sample_ids
        self.assertEqual(sample.state, 'draft')
        self.assertTrue(sample.name.startswith('RS/'))
        self.assertEqual(sample.qa_release_id, release)
        self.assertEqual(sample.production_id, production)
        self.assertEqual(sample.location_id, self.location)
        self.assertEqual(sample.container, 'Amber glass bottle')
        self.assertEqual(sample.retention_period_months, 12)
        self.assertEqual(sample.exam_interval_months, 6)
        self.assertEqual(sample.disposal_due_date, date(2021, 1, 31))
        self.assertFalse(lot.show_retain_sample)
        self.assertEqual(release.retention_sample_count, 1)
        action = release.action_view_retention_samples()
        self.assertEqual(action['res_id'], sample.id)

    def test_create_requires_released_and_single(self):
        """Only released batches get a sample, and only one."""
        lot = self.create_lot(name='RS-NOT-RELEASED')
        with self.assertRaises(UserError):
            lot.action_create_retention_sample()
        sample = self.draft_sample()
        with self.assertRaises(UserError):
            sample.lot_id.action_create_retention_sample()

    def test_company_default_location(self):
        """Without a product location, the company default is proposed."""
        self.product_tmpl.retention_location_id = False
        sample = self.draft_sample()
        self.assertEqual(sample.location_id, self.env.company.pharma_retention_location_id)

    def test_confirm(self):
        """Confirming records who retained it and schedules the examination."""
        sample = self.draft_sample()
        sample.lot_id.activity_schedule(
            'pharma_retention_sample.mail_activity_retain_sample', user_id=self.operator.id)
        sample.with_user(self.operator).action_confirm()
        self.assertEqual(sample.state, 'retained')
        self.assertEqual(sample.retained_by, self.operator)
        self.assertTrue(sample.retained_on)
        self.assertTrue(sample.next_exam_date)
        self.assertFalse(sample.lot_id.activity_ids)
        self.assertEqual(sample.remaining_qty, 10.0)
        with self.assertRaises(UserError):
            sample.action_confirm()

    def test_confirm_without_exam_interval(self):
        """A zero examination interval leaves no examination scheduled."""
        self.product_tmpl.retention_exam_interval_months = 0
        sample = self.retained_sample()
        self.assertFalse(sample.next_exam_date)

    def test_confirm_checks(self):
        """A location and a positive quantity are needed to confirm."""
        sample = self.draft_sample(qty=0.0)
        with self.assertRaises(UserError):
            sample.action_confirm()
        sample.location_id = False
        with self.assertRaises(UserError):
            sample.action_confirm()

    def test_protected_fields(self):
        """Recorded facts are not edited directly; disposed samples are frozen."""
        sample = self.draft_sample()
        with self.assertRaises(UserError):
            sample.state = 'retained'
        sample.action_confirm()
        with self.assertRaises(UserError):
            sample.retained_qty = 5.0
        sample.container = 'Blister in carton'
        self.assertEqual(sample.container, 'Blister in carton')
        with self.assertRaises(UserError):
            sample.unlink()

    def test_actions(self):
        """Batch and sample navigation actions."""
        sample = self.draft_sample()
        self.assertEqual(sample.action_view_lot()['res_id'], sample.lot_id.id)
        self.assertEqual(sample.lot_id.action_view_retention_samples()['res_id'], sample.id)
        with self.assertRaises(UserError):
            sample.action_record_withdrawal()
        sample.action_confirm()
        action = sample.action_record_withdrawal()
        self.assertEqual(action['context']['default_sample_id'], sample.id)
        with self.assertRaises(UserError):
            sample.with_user(self.operator).action_open_disposal_wizard()
        action = sample.with_user(self.qa_user).action_open_disposal_wizard()
        self.assertEqual(action['res_model'], 'pharma.retention.disposal.wizard')

    def test_access(self):
        """Pharma users read the register; nobody deletes from it."""
        sample = self.draft_sample()
        self.assertEqual(sample.with_user(self.qa_user).read(['state'])[0]['state'], 'draft')
        with self.assertRaises(AccessError):
            sample.with_user(self.operator).check_access('unlink')

    def test_cron_missing_retention(self):
        """Released batches without a confirmed sample get one reminder each."""
        lot = self.released_lot(name='RS-MISSING')
        lot.status_changed_by = self.qa_user
        done = self.retained_sample(lot=self.released_lot(name='RS-DONE')).lot_id
        Sample = self.env['pharma.retention.sample']
        activity_type = self.env.ref('pharma_retention_sample.mail_activity_retain_sample')
        Sample._cron_pharma_missing_retention()
        Sample._cron_pharma_missing_retention()
        reminders = lot.activity_ids.filtered(lambda a: a.activity_type_id == activity_type)
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders.user_id, self.qa_user)
        self.assertFalse(done.activity_ids)
        missing = self.env['stock.lot'].search(
            self.env['stock.lot']._pharma_retention_missing_domain())
        self.assertIn(lot, missing)
        self.assertNotIn(done, missing)

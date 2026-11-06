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
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import PharmaTraceabilityCommon


@tagged('post_install', '-at_install')
class TestQaRelease(PharmaTraceabilityCommon):
    """Sending batches to the QA Release Queue and releasing them."""

    def test_queue_and_release(self):
        """QA queues an eligible batch and releases it; a locked CoA is issued."""
        release = self.queued_release()
        mo = release.production_id
        self.assertEqual(release.state, 'draft')
        self.assertTrue(release.name.startswith('QA/RELEASE/'))
        self.assertEqual(release.lot_id, mo.lot_producing_ids)
        self.assertTrue(mo.pharma_qa_release_exists)
        self.assertTrue(release.bmr_completed and release.fg_qc_passed)
        self.assertTrue(release.all_ipqc_passed and release.yield_within_threshold)
        self.assertEqual(release.overall_status, 'all_clear')
        self.assertEqual(release.fg_qc_status, 'passed')
        self.assertEqual(release.fg_qc_reviewed_by, self.qa_user)
        self.assertEqual((release.expected_yield, release.yield_flag), (10.0, 'within'))
        self.assertEqual((release.bmr_count, release.qc_test_count, release.coa_count), (1, 1, 0))
        release.with_user(self.qa_user).action_confirm()
        self.assertEqual(release.state, 'released')
        self.assertEqual(release.lot_id.lot_status, 'released')
        coa = release.coa_id
        self.assertTrue(coa.is_locked)
        self.assertEqual(coa.released_by, self.qa_user)
        self.assertEqual(coa.coa_line_ids.status, 'pass')
        release.invalidate_recordset(['coa_count'])
        self.assertEqual(release.coa_count, 1)
        # Released records are skipped on a second confirm.
        release.with_user(self.qa_user).action_confirm()
        self.assertEqual(self.env['pharma.coa'].search_count([('batch_id', '=', mo.id)]), 1)

    def test_queue_checks(self):
        """Only QA queues, only eligible batches, and only once."""
        mo = self.completed_mo()
        with self.assertRaises(ValidationError):
            mo.with_user(self.qa_user).action_qa_release()
        self.pass_order(self.fg_order(mo))
        with self.assertRaises(UserError):
            mo.with_user(self.operator).action_qa_release()
        mo.with_user(self.qa_user).action_qa_release()
        with self.assertRaises(ValidationError):
            mo.with_user(self.qa_user).action_qa_release()

    def test_queue_blocked_by_open_deviation(self):
        """An open deviation on the batch blocks queueing and release."""
        mo = self.eligible_mo()
        deviation = self.create_deviation(batch_id=mo.id)
        with self.assertRaises(ValidationError):
            mo.with_user(self.qa_user).action_qa_release()
        deviation.sudo().status = 'closed'
        mo.with_user(self.qa_user).action_qa_release()
        release = self.env['pharma.qa.release'].search([('production_id', '=', mo.id)])
        deviation = self.create_deviation(batch_id=mo.id)
        self.env['pharma.capa'].create(
            {
                'deviation_id': deviation.id,
                'capa_type': 'corrective',
                'assigned_to': self.qa_user.id,
            }
        )
        self.assertFalse(release.no_open_deviations)
        self.assertFalse(release.no_open_capas)
        self.assertEqual(release.overall_status, 'pending')
        self.assertEqual(release.deviation_count, 2)
        with self.assertRaises(ValidationError):
            release.with_user(self.qa_user).action_confirm()

    def test_checklist_counts_lot_deviations(self):
        """A deviation raised on the lot without a batch reference still clears the checklist."""
        release = self.queued_release()
        deviation = self.create_deviation(lot_id=release.lot_id.id)
        release.invalidate_recordset()
        self.assertFalse(release.no_open_deviations)
        self.assertEqual(release.overall_status, 'pending')
        self.assertEqual(release.deviation_count, 1)
        deviation.sudo().status = 'closed'
        release.invalidate_recordset()
        self.assertTrue(release.no_open_deviations)
        self.assertEqual(release.overall_status, 'all_clear')

    def test_release_with_pending_ipqc(self):
        """An IPQC check with no recorded value goes on the CoA as Pending."""
        release = self.queued_release()
        bmr = release.production_id.bmr_ids
        spec_line = self.env['pharma.qc.spec.line'].search(
            [('spec_id.product_id', '=', self.tablet_tmpl.id)], limit=1
        )
        check = (
            self.env['pharma.ipqc.result']
            .sudo()
            .create(
                {
                    'bmr_id': bmr.id,
                    'step_id': bmr.step_ids[0].id,
                    'parameter_id': spec_line.id,
                }
            )
        )
        self.assertFalse(check.result)
        release.with_user(self.qa_user).action_confirm()
        self.assertEqual(release.state, 'released')
        self.assertEqual(release.coa_id.coa_line_ids.mapped('status'), ['pass', 'pending'])

    def test_release_requires_qa(self):
        """Operators cannot release, nor create queue records."""
        release = self.queued_release()
        with self.assertRaises(UserError):
            release.with_user(self.operator).action_confirm()
        with self.assertRaises(AccessError):
            self.env['pharma.qa.release'].with_user(self.qa_user).check_access('create')

    def test_low_yield(self):
        """A yield below 90% is flagged on the release record."""
        mo = self.completed_mo(produced=8.0)
        mo.qty_producing = 8.0
        self.pass_order(self.fg_order(mo))
        mo.with_user(self.qa_user).action_qa_release()
        release = self.env['pharma.qa.release'].search([('production_id', '=', mo.id)])
        self.assertEqual(release.yield_flag, 'out')
        self.assertFalse(release.yield_within_threshold)

    def test_navigation(self):
        """Smart buttons open the batch records."""
        release = self.queued_release()
        mo = release.production_id
        self.assertEqual(release.action_view_bmr()['domain'], [('production_id', '=', mo.id)])
        self.assertIn(release.lot_id.id, release.action_view_qc_tests()['domain'][0][2])
        self.assertEqual(release.action_view_deviations()['res_model'], 'pharma.deviation')
        self.assertEqual(release.action_view_capas()['res_model'], 'pharma.capa')
        self.assertEqual(release.action_view_coa()['domain'], [('lot_id', '=', release.lot_id.id)])
        action = release.action_view_genealogy()
        self.assertEqual((action['res_model'], action['res_id']), ('stock.lot', release.lot_id.id))
        release.lot_id = False
        with self.assertRaises(ValidationError):
            release.action_view_genealogy()

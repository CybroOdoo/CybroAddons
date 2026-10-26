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
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, tagged

from .common import PharmaTestCommon


@tagged('post_install', '-at_install')
class TestQcSpecification(PharmaTestCommon):
    """QC specifications and their parameters."""

    def test_spec_numbering_and_versions(self):
        """A spec is named from its product and stage, and versions count up."""
        self.assertTrue(self.spec.name.startswith('SPEC/PARACETAMOL API/INCOMING/'))
        self.assertEqual(self.spec.version, '1.0')
        second = self.create_spec(self.product_tmpl, 'incoming')
        self.assertEqual(second.version, '2.0')
        self.spec.version = 'abc'
        self.assertEqual(self.env['pharma.qc.spec']._next_version(self.product_tmpl.id, 'incoming'), '3.0')
        self.assertEqual(self.env['pharma.qc.spec']._next_version(False, 'incoming'), '1.0')

    def test_spec_onchange_version(self):
        """The form proposes the next version for the product and stage."""
        form = Form(self.env['pharma.qc.spec'])
        form.product_id = self.product_tmpl
        form.stage = 'incoming'
        self.assertEqual(form.version, '2.0')

    def test_spec_workflow(self):
        """QA approves, obsoletes and resets a specification; others cannot."""
        spec = self.create_spec(self.product_tmpl, 'finished')
        spec.action_submit_review()
        self.assertEqual(spec.state, 'review')
        with self.assertRaises(AccessError):
            spec.with_user(self.operator).action_approve()
        spec.with_user(self.qa_user).action_approve()
        self.assertEqual((spec.state, spec.approved_by), ('approved', self.qa_user))
        with self.assertRaises(AccessError):
            spec.with_user(self.operator).action_obsolete()
        spec.with_user(self.qa_user).action_obsolete()
        self.assertEqual(spec.state, 'obsolete')
        with self.assertRaises(AccessError):
            spec.with_user(self.operator).action_reset_draft()
        spec.with_user(self.qa_user).action_reset_draft()
        self.assertEqual(spec.state, 'draft')

    def test_spec_constraints(self):
        """Approval needs an approver, dates cannot be past, parameters are required."""
        spec = self.create_spec(self.product_tmpl, 'finished')
        with self.assertRaises(ValidationError):
            spec.write({'state': 'approved'})
        with self.assertRaises(ValidationError):
            spec.write({'effective_date': fields.Date.today() - timedelta(days=1)})
        with self.assertRaises(ValidationError):
            spec.write({'parameter_ids': [(5, 0, 0)]})

    def test_spec_line_limits(self):
        """Limits cannot be negative and Max cannot be below Min."""
        line = self.spec.parameter_ids
        with self.assertRaises(ValidationError):
            line.write({'min_value': -1})
        with self.assertRaises(ValidationError):
            line.write({'min_value': 10, 'max_value': 5})


@tagged('post_install', '-at_install')
class TestQcTestOrder(PharmaTestCommon):
    """QC test orders and their result lines."""

    def test_create_loads_spec_and_lines(self):
        """A new order takes the approved spec and builds its result lines."""
        order = self.create_order()
        self.assertEqual(order.spec_id, self.spec)
        self.assertTrue(order.name.startswith('QC') or order.name != '/')
        line = order.result_line_ids
        self.assertEqual((line.expected_min, line.expected_max, line.status), (98.0, 102.0, 'pending'))
        self.assertEqual(line.value_origin, 'manual')

    def test_create_without_spec_fails(self):
        """An order for a stage with no approved spec is refused."""
        with self.assertRaises(ValidationError):
            self.create_order(stage='finished')

    def test_onchange_product_stage_and_spec(self):
        """The form loads the spec and generates its result lines."""
        form = Form(self.env['pharma.qc.test.order'])
        form.product_id = self.product_tmpl
        form.lot_id = self.create_lot()
        form.stage = 'incoming'
        self.assertEqual(form.spec_id, self.spec)
        self.assertEqual(len(form.result_line_ids), 1)
        form.stage = 'finished'
        self.assertFalse(form.spec_id)
        form.product_id = self.env['product.template']
        self.assertFalse(form.spec_id)

    def test_spec_change_regenerates_lines(self):
        """Changing the spec of a draft order rebuilds its lines."""
        order = self.create_order()
        other = self.create_spec(self.product_tmpl, 'incoming', 1.0, 2.0)
        order.write({'spec_id': other.id})
        self.assertEqual(order.result_line_ids.expected_max, 2.0)

    def test_pass_flow(self):
        """Start, enter a passing result and approve: the lot is approved."""
        order = self.create_order()
        line = order.result_line_ids
        with self.assertRaises(ValidationError):
            line.write({'actual_value': 100.0})
        order.action_start_test()
        self.assertEqual((order.status, order.entered_by), ('in_progress', self.env.user))
        with self.assertRaises(ValidationError):
            order.action_start_test()
        with self.assertRaises(ValidationError):
            order.with_user(self.qa_user).action_approve()
        line.write({'actual_value': 100.0})
        self.assertEqual((line.status, line.result_entered), ('pass', True))
        with self.assertRaises(ValidationError):
            order.write({'stage': 'finished'})
        with self.assertRaises(AccessError):
            order.with_user(self.operator).action_approve()
        order.with_user(self.qa_user).action_approve()
        self.assertEqual(order.status, 'passed')
        self.assertEqual(order.lot_id.lot_status, 'approved')
        with self.assertRaises(ValidationError):
            order.with_user(self.qa_user).action_approve()
        self.assertTrue(self.product_tmpl.has_passed_qc_test)

    def test_analyst_cannot_review(self):
        """The analyst who entered the results cannot approve or reject them."""
        order = self.create_order()
        order.with_user(self.qa_user).action_start_test()
        order.result_line_ids.write({'actual_value': 100.0})
        with self.assertRaises(ValidationError):
            order.with_user(self.qa_user).action_approve()
        with self.assertRaises(ValidationError):
            order.with_user(self.qa_user).action_reject()
        self.assertEqual(order.status, 'in_progress')

    def test_in_process_order_finds_ipqc_spec(self):
        """An in-process test order loads the product's approved IPQC spec."""
        ipqc_spec = self.create_spec(self.product_tmpl, 'ipqc', 1.0, 5.0)
        ipqc_spec.action_submit_review()
        ipqc_spec.with_user(self.qa_user).action_approve()
        order = self.create_order(stage='ipqc')
        self.assertEqual(order.spec_id, ipqc_spec)
        self.assertEqual(order.result_line_ids.parameter_id, ipqc_spec.parameter_ids)

    def test_reject_flow(self):
        """QA rejects an order in progress: the lot is rejected."""
        order = self.create_order()
        with self.assertRaises(ValidationError):
            order.with_user(self.qa_user).action_reject()
        order.action_start_test()
        with self.assertRaises(AccessError):
            order.with_user(self.operator).action_reject()
        order.with_user(self.qa_user).action_reject()
        self.assertEqual((order.status, order.lot_id.lot_status), ('failed', 'rejected'))

    def test_views_and_counts(self):
        """The stock move and OOS buttons open filtered lists."""
        order = self.create_order()
        self.assertEqual(order.stock_move_line_count, 0)
        self.assertEqual(order.oos_investigation_count, 0)
        self.assertEqual(order.action_view_stock_moves()['res_model'], 'stock.move.line')
        self.assertEqual(order.action_view_oos_investigations()['res_model'], 'pharma.oos.investigation')

    def test_result_line_onchanges(self):
        """Picking a parameter loads its limits; typing a value marks it entered."""
        order = self.create_order()
        line = order.result_line_ids
        line.parameter_id = False
        line._onchange_parameter_id()
        self.assertEqual((line.expected_min, line.has_min), (0.0, False))
        line.parameter_id = self.spec.parameter_ids
        line._onchange_parameter_id()
        self.assertEqual((line.expected_max, line.has_max), (102.0, True))
        line._onchange_actual_value()
        self.assertTrue(line.result_entered)

    def test_zero_spec_result_is_entered(self):
        """A zero value against a zero spec counts as entered on create."""
        order = self.create_order()
        line = self.env['pharma.qc.result.line'].create({
            'test_order_id': order.id, 'actual_value': 0.0,
        })
        self.assertTrue(line.result_entered)


@tagged('post_install', '-at_install')
class TestOosInvestigation(PharmaTestCommon):
    """OOS investigations raised by out-of-specification results."""

    def _oos_order(self):
        """An order in progress whose result is out of specification."""
        order = self.create_order()
        order.action_start_test()
        order.result_line_ids.write({'actual_value': 90.0})
        return order

    def test_oos_raises_investigation(self):
        """An OOS result opens a Phase I investigation and blocks approval."""
        order = self._oos_order()
        inv = order.oos_investigation_ids
        self.assertEqual((order.status, inv.phase, order.oos_investigation_count),
                         ('under_investigation', 'phase_1', 1))
        self.assertTrue(inv.name and inv.name != '/')
        self.assertIn('between 98.0000 and 102.0000', inv.conclusion)
        self.assertEqual(inv.action_view_test_order()['res_id'], order.id)
        with self.assertRaises(ValidationError):
            order.with_user(self.qa_user).action_approve()

    def test_conclusion_compute_and_inverse(self):
        """The conclusion text follows the limits and keeps the written notes."""
        inv = self._oos_order().oos_investigation_ids
        line = inv.result_line_id
        inv.conclusion = inv.conclusion + '\n\nConclusion:\nAnalyst error ruled out'
        self.assertEqual(inv.conclusion_notes, 'Analyst error ruled out')
        inv.conclusion = 'The test parameter X was 1, but the actual value was 2.\nSecond line'
        self.assertEqual(inv.conclusion_notes, 'Second line')
        inv.conclusion = 'The test parameter X was 1, but the actual value was 2.'
        self.assertEqual(inv.conclusion_notes, '')
        inv.conclusion = 'Free text'
        self.assertEqual(inv.conclusion_notes, 'Free text')
        # has_min / has_max are not in the compute's depends: recompute by hand.
        for has_min, has_max, text in ((True, False, 'at least'), (False, True, 'at most'),
                                       (False, False, 'out-of-specification')):
            line.write({'has_min': has_min, 'has_max': has_max})
            inv.invalidate_recordset(['conclusion'])
            self.assertIn(text, inv.conclusion)

    def test_invalidate_and_retest(self):
        """A lab error invalidates the result and returns the order to testing."""
        order = self._oos_order()
        inv = order.oos_investigation_ids
        with self.assertRaises(AccessError):
            inv.with_user(self.operator).action_invalidate_retest()
        with self.assertRaises(ValidationError):
            inv.with_user(self.qa_user).action_invalidate_retest()
        inv.lab_error_found = True
        with self.assertRaises(ValidationError):
            inv.with_user(self.qa_user).action_escalate_to_phase_2()
        inv.with_user(self.qa_user).action_invalidate_retest()
        self.assertTrue(inv.closed_on)
        self.assertEqual((order.status, order.result_line_ids.result_entered), ('in_progress', False))
        with self.assertRaises(ValidationError):
            inv.with_user(self.qa_user).action_invalidate_retest()
        with self.assertRaises(ValidationError):
            inv.write({'phase': 'phase_2'})
        order.result_line_ids.write({'actual_value': 100.0})
        order.with_user(self.qa_user).action_approve()
        self.assertEqual(order.status, 'passed')

    def test_phase_2_release(self):
        """Phase II closed with Release passes the order and allows approval."""
        order = self._oos_order()
        inv = order.oos_investigation_ids
        with self.assertRaises(AccessError):
            inv.with_user(self.operator).action_escalate_to_phase_2()
        with self.assertRaises(ValidationError):
            inv.with_user(self.qa_user).action_close_investigation()
        inv.with_user(self.qa_user).action_escalate_to_phase_2()
        self.assertEqual(inv.phase, 'phase_2')
        with self.assertRaises(ValidationError):
            inv.with_user(self.qa_user).action_escalate_to_phase_2()
        with self.assertRaises(ValidationError):
            inv.with_user(self.qa_user).action_invalidate_retest()
        with self.assertRaises(ValidationError):
            inv.write({'closed_on': fields.Datetime.now()})
        with self.assertRaises(ValidationError):
            inv.with_user(self.qa_user).action_close_investigation()
        inv.disposition = 'release'
        with self.assertRaises(AccessError):
            inv.with_user(self.operator).action_close_investigation()
        inv.with_user(self.qa_user).action_close_investigation()
        self.assertEqual(order.status, 'passed')
        with self.assertRaises(ValidationError):
            inv.with_user(self.qa_user).action_close_investigation()
        with self.assertRaises(ValidationError):
            inv.with_user(self.qa_user).action_escalate_to_phase_2()

    def test_phase_2_reject(self):
        """Phase II closed with Reject fails the order and segregates the lot."""
        location = self.env['stock.location'].create({
            'name': 'Rejected', 'usage': 'internal',
            'location_id': self.env.ref('stock.stock_location_stock').id,
        })
        self.env.company.pharma_rejected_location_id = location
        order = self._oos_order()
        self.env['stock.quant']._update_available_quantity(
            self.product, self.env.ref('stock.stock_location_stock'), 5.0, lot_id=order.lot_id)
        inv = order.oos_investigation_ids
        inv.with_user(self.qa_user).action_escalate_to_phase_2()
        inv.disposition = 'reject'
        inv.with_user(self.qa_user).action_close_investigation()
        self.assertEqual(order.status, 'failed')
        quant = self.env['stock.quant'].search([('lot_id', '=', order.lot_id.id), ('quantity', '>', 0)])
        self.assertEqual(quant.location_id, location)

    def test_release_with_other_rejected(self):
        """A Release closes as failed when another result was rejected."""
        spec = self.create_spec(self.product_tmpl, 'incoming')
        spec.write({'parameter_ids': [(0, 0, {'parameter_name': 'pH', 'min_value': 5, 'max_value': 7})]})
        spec.action_submit_review()
        spec.with_user(self.qa_user).action_approve()
        order = self.create_order()
        order.action_start_test()
        first, second = order.result_line_ids
        first.write({'actual_value': 1.0})
        second.write({'actual_value': 99.0})
        Investigation = self.env['pharma.oos.investigation']
        inv_first = Investigation.search([('result_line_id', '=', first.id)])
        inv_second = Investigation.search([('result_line_id', '=', second.id)])
        for inv in (inv_first, inv_second):
            inv.with_user(self.qa_user).action_escalate_to_phase_2()
        inv_first.disposition = 'reject'
        inv_first.with_user(self.qa_user).action_close_investigation()
        order.status = 'under_investigation'
        inv_second.disposition = 'release'
        inv_second.with_user(self.qa_user).action_close_investigation()
        self.assertEqual(order.status, 'failed')

    def test_approve_oos_needs_resolution(self):
        """Approval checks the OOS investigation outcome of each line."""
        order = self._oos_order()
        inv = order.oos_investigation_ids
        inv.with_user(self.qa_user).action_escalate_to_phase_2()
        inv.write({'disposition': 'reject', 'closed_on': fields.Datetime.now()})
        with self.assertRaises(ValidationError):
            order.with_user(self.qa_user).action_approve()
        inv.unlink()
        with self.assertRaises(ValidationError):
            order.with_user(self.qa_user).action_approve()

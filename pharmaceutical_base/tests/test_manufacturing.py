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
from odoo.tests import Form, tagged

from .common import PharmaTestCommon


class PharmaManufacturingCommon(PharmaTestCommon):
    """A finished product with an approved two-operation formula."""

    @classmethod
    def setUpClass(cls):
        """Create the work centre, the finished product and its approved BoM."""
        super().setUpClass()
        cls.workcenter = cls.env['mrp.workcenter'].create({'name': 'Granulation Suite'})
        cls.tablet_tmpl = cls.env['product.template'].create({
            'name': 'Paracetamol Tablets', 'is_storable': True,
        })
        cls.tablet = cls.tablet_tmpl.product_variant_id
        cls.bom = cls.create_bom(cls.tablet_tmpl, approve=True)
        cls.ipqc_spec = cls.create_spec(cls.tablet_tmpl, 'ipqc', 1.0, 5.0)

    @classmethod
    def create_bom(cls, template, lines=None, approve=False):
        """A two-operation formula for ``template``, approved by QA when asked."""
        bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': template.id,
            'product_qty': 1,
            'bom_line_ids': lines or [],
            'operation_ids': [
                (0, 0, {'name': 'Granulate', 'workcenter_id': cls.workcenter.id, 'sequence': 10}),
                (0, 0, {'name': 'Compress', 'workcenter_id': cls.workcenter.id, 'sequence': 20}),
            ],
        })
        if approve:
            bom.with_user(cls.qa_user).sudo().action_approve_formula()
        return bom

    def create_mo(self, qty=10.0, bom=None):
        """Create a draft manufacturing order for the tablets."""
        return self.env['mrp.production'].create({
            'product_id': self.tablet.id,
            'bom_id': (bom if bom is not None else self.bom).id,
            'product_qty': qty,
        })

    def confirmed_bmr(self):
        """Confirm a new order and return its generated BMR."""
        mo = self.create_mo()
        mo.action_confirm()
        return mo.bmr_ids


@tagged('post_install', '-at_install')
class TestFormula(PharmaManufacturingCommon):
    """Pharma formula (BoM) approval and line merging."""

    def test_formula_workflow(self):
        """QA approves, obsoletes and resets a formula; the version counts up."""
        bom = self.create_bom(self.tablet_tmpl)
        self.assertEqual(bom.formula_status, 'draft')
        for action in ('action_approve_formula', 'action_obsolete_formula', 'action_reset_draft'):
            with self.assertRaises(AccessError):
                getattr(bom.with_user(self.operator), action)()
        qa_bom = bom.with_user(self.qa_user).sudo()
        qa_bom.action_approve_formula()
        self.assertEqual((bom.formula_status, bom.approved_by), ('approved', self.qa_user))
        qa_bom.action_obsolete_formula()
        self.assertEqual(bom.formula_status, 'obsolete')
        qa_bom.action_reset_draft()
        self.assertEqual((bom.formula_status, bom.formula_version, bom.approved_by.id),
                         ('draft', 2, False))

    def test_formula_constraints(self):
        """An approved formula needs an approver and at least one operation."""
        bom = self.env['mrp.bom'].create({'product_tmpl_id': self.tablet_tmpl.id})
        with self.assertRaises(ValidationError):
            bom.write({'formula_status': 'approved'})
        with self.assertRaises(ValidationError):
            bom.with_user(self.qa_user).sudo().action_approve_formula()

    def test_formula_merges_identical_lines(self):
        """Identical component lines are merged into one, on create and on write."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.tablet_tmpl.id,
            'bom_line_ids': [(0, 0, {'product_id': self.product.id, 'product_qty': 1}),
                             (0, 0, {'product_id': self.product.id, 'product_qty': 2})],
        })
        self.assertEqual(bom.bom_line_ids.product_qty, 3)
        bom.write({'bom_line_ids': [(0, 0, {'product_id': self.product.id, 'product_qty': 4})]})
        self.assertEqual(bom.bom_line_ids.product_qty, 7)


@tagged('post_install', '-at_install')
class TestManufacturingOrder(PharmaManufacturingCommon):
    """Manufacturing order gates and BMR generation."""

    def test_confirm_requires_approved_formula(self):
        """A draft formula blocks confirmation."""
        bom = self.create_bom(self.tablet_tmpl)
        with self.assertRaises(UserError):
            self.create_mo(bom=bom).action_confirm()

    def test_confirm_requires_component_qc(self):
        """Components without a passed QC test order block confirmation."""
        bom = self.create_bom(self.tablet_tmpl, [(0, 0, {'product_id': self.product.id, 'product_qty': 1})],
                              approve=True)
        mo = self.create_mo(bom=bom)
        self.assertEqual(mo.move_raw_ids.qc_test_order_status, 'fail')
        self.assertEqual(mo.pharma_allowed_component_ids, self.product)
        with self.assertRaises(UserError):
            mo.action_confirm()

    def test_confirm_creates_bmr(self):
        """Confirmation generates a draft BMR with one step per operation."""
        mo = self.create_mo()
        with self.assertRaises(UserError):
            mo.button_mark_done()
        mo.action_confirm()
        bmr = mo.bmr_ids
        self.assertEqual((mo.bmr_count, bmr.status, bmr.batch_no), (1, 'draft', mo.name))
        self.assertEqual(bmr.step_ids.mapped('description'), ['Granulate', 'Compress'])
        self.assertEqual(bmr.yield_expected, 10.0)
        self.assertFalse(mo.pharma_bmr_completed)
        with self.assertRaises(UserError):
            mo.action_create_bmr()
        action = mo.action_view_bmr()
        self.assertEqual((action['res_id'], action['context']['create']), (bmr.id, False))

    def test_bmr_without_formula(self):
        """An order without a formula gets a single standard step."""
        loose = self.env['product.product'].create({'name': 'Loose Powder', 'is_storable': True})
        mo = self.env['mrp.production'].create({'product_id': loose.id, 'product_qty': 2})
        self.assertFalse(mo.bom_id)
        bmr = mo.action_create_bmr()
        self.assertEqual(len(bmr.step_ids), 1)
        bmr.unlink()
        action = mo.action_view_bmr()
        self.assertEqual(action['domain'], [('production_id', '=', mo.id)])

    def test_qc_and_release_actions(self):
        """QC test orders, QA release eligibility and the release placeholder."""
        mo = self.create_mo()
        lot = self.create_lot()
        self.create_order(lot=lot)
        mo.move_raw_ids = [(0, 0, {
            'product_id': self.product.id, 'product_uom_qty': 1,
            'location_id': mo.location_src_id.id, 'location_dest_id': mo.production_location_id.id,
        })]
        self.assertEqual(mo.qc_test_order_count, 1)
        action = mo.action_view_qc_test_orders()
        self.assertEqual(action['view_mode'], 'form')
        self.assertFalse(mo.qa_release_eligible)
        self.assertFalse(mo.pharma_qa_release_exists)
        Production = self.env['mrp.production']
        self.assertEqual(Production._search_qa_release_eligible('=', True), [('id', 'in', [])])
        self.assertEqual(Production._search_qa_release_eligible('!=', True), [])
        with self.assertRaises(UserError):
            mo.action_qa_release()

    def test_order_merges_identical_moves(self):
        """Identical component moves on a draft order are merged."""
        mo = self.create_mo()
        vals = {
            'product_id': self.product.id, 'product_uom_qty': 1,
            'location_id': mo.location_src_id.id, 'location_dest_id': mo.production_location_id.id,
        }
        mo.write({'move_raw_ids': [(0, 0, vals), (0, 0, dict(vals, product_uom_qty=2))]})
        self.assertEqual(mo.move_raw_ids.product_uom_qty, 3)


@tagged('post_install', '-at_install')
class TestBatchRecord(PharmaManufacturingCommon):
    """BMR execution: steps, holds, IPQC and completion."""

    def test_bmr_start_hold_resume(self):
        """A BMR starts, goes on hold and resumes from the right states only."""
        bmr = self.confirmed_bmr()
        self.assertTrue(bmr.name and bmr.name != 'New')
        for action in ('action_hold', 'action_resume'):
            with self.assertRaises(UserError):
                getattr(bmr, action)()
        bmr.action_start()
        with self.assertRaises(UserError):
            bmr.action_start()
        bmr.action_hold()
        self.assertEqual(bmr.status, 'on_hold')
        bmr.step_ids[0].action_hold()
        with self.assertRaises(UserError):
            bmr.action_resume()
        bmr.step_ids[0].action_release_hold()
        bmr.action_resume()
        self.assertEqual(bmr.status, 'in_progress')

    def test_bmr_start_needs_steps(self):
        """A BMR without steps cannot be started."""
        mo = self.env['mrp.production'].create({'product_id': self.tablet.id, 'product_qty': 1})
        bmr = self.env['pharma.bmr'].create({
            'production_id': mo.id, 'product_id': self.tablet_tmpl.id, 'batch_no': 'B1',
        })
        with self.assertRaises(UserError):
            bmr.action_start()

    def test_bmr_locked_fields(self):
        """The order and product of a BMR cannot change; IPQC off clears the checks."""
        bmr = self.confirmed_bmr()
        with self.assertRaises(UserError):
            bmr.write({'production_id': self.create_mo().id})
        with self.assertRaises(UserError):
            bmr.write({'product_id': self.product_tmpl.id})
        with self.assertRaises(UserError):
            bmr.step_ids[0].write({'bmr_id': self.confirmed_bmr().id})
        bmr.write({'enable_ipqc': False})
        draft = self.env['pharma.bmr'].new({'enable_ipqc': False})
        draft._onchange_enable_ipqc()
        self.assertFalse(draft.ipqc_ids)
        self.assertEqual(bmr.action_view_steps()['domain'], [('bmr_id', '=', bmr.id)])
        self.assertEqual(bmr.action_view_ipqc()['domain'], [('bmr_id', '=', bmr.id)])
        self.assertEqual((bmr.step_count, bmr.ipqc_count), (2, 0))

    def test_step_signoffs(self):
        """Operator then supervisor sign a step; each gate is enforced."""
        bmr = self.confirmed_bmr()
        bmr.action_start()
        step = bmr.step_ids[0]
        self.assertEqual(step.name, '10 - Granulate')
        with self.assertRaises(AccessError):
            step.with_user(self.operator).action_supervisor_sign()
        with self.assertRaises(UserError):
            step.with_user(self.qa_user).action_supervisor_sign()
        step.with_user(self.operator).action_operator_sign()
        self.assertTrue(bmr.any_step_operator_signed)
        with self.assertRaises(UserError):
            step.action_operator_sign()
        step.with_user(self.qa_user).action_supervisor_sign()
        self.assertEqual((step.status, step.supervisor_id), ('done', self.qa_user))
        with self.assertRaises(UserError):
            step.with_user(self.qa_user).action_supervisor_sign()
        with self.assertRaises(UserError):
            step.action_operator_sign()
        with self.assertRaises(UserError):
            step.action_hold()

    def test_step_hold_cascade(self):
        """Holding a step holds the later steps and the BMR; release restores them."""
        bmr = self.confirmed_bmr()
        bmr.action_start()
        first, second = bmr.step_ids
        first.action_hold()
        self.assertEqual((second.status, second.hold_source_step_id, bmr.status),
                         ('hold', first, 'on_hold'))
        with self.assertRaises(UserError):
            first.action_hold()
        with self.assertRaises(UserError):
            second.action_operator_sign()
        with self.assertRaises(UserError):
            second.action_release_hold()
        first.action_release_hold()
        self.assertEqual((first.status, second.status), ('pending', 'pending'))
        with self.assertRaises(UserError):
            first.action_release_hold()
        step = self.env['pharma.bmr.step'].new({'sequence': 5, 'description': ''})
        self.assertEqual(step.name, 'Step 5')

    def _ipqc(self, step, value=0.0):
        """Record an IPQC check on an operator-signed step."""
        form = Form(self.env['pharma.ipqc.result'])
        form.bmr_id = step.bmr_id
        form.step_id = step
        form.parameter_id = self.ipqc_spec.parameter_ids
        if value:
            form.actual_value = value
        return form.save()

    def test_ipqc_checks(self):
        """IPQC results pass or fail against their limits and gate sign-off."""
        bmr = self.confirmed_bmr()
        bmr.write({'enable_ipqc': True})
        bmr.action_start()
        step = bmr.step_ids[0]
        with self.assertRaises(ValidationError):
            self.env['pharma.ipqc.result'].create({
                'bmr_id': bmr.id, 'step_id': step.id, 'parameter_id': self.ipqc_spec.parameter_ids.id,
            })
        step.action_operator_sign()
        check = self._ipqc(step)
        self.assertEqual((check.expected_min, check.expected_max, check.result), (1.0, 5.0, False))
        with self.assertRaises(UserError):
            check.action_sign()
        with self.assertRaises(UserError):
            step.with_user(self.qa_user).action_supervisor_sign()
        with self.assertRaises(ValidationError):
            self.env['pharma.ipqc.result'].create({
                'bmr_id': bmr.id, 'step_id': step.id, 'parameter_id': self.ipqc_spec.parameter_ids.id,
            })
        with self.assertRaises(ValidationError):
            check.write({'expected_min': 9.0})
        check.write({'actual_value': 9.0})
        self.assertEqual(check.result, 'fail')
        check.action_sign()
        self.assertEqual((step.status, bmr.status), ('hold', 'on_hold'))
        with self.assertRaises(UserError):
            check.action_sign()
        with self.assertRaises(UserError):
            bmr.action_resume()
        check.write({'result': 'pass'})
        self.assertEqual((step.status, bmr.status), ('pending', 'in_progress'))
        check.write({'result': 'fail'})
        self.assertEqual(step.status, 'hold')

    def test_ipqc_duplicate_warning(self):
        """Picking a parameter already recorded on the step warns and clears it."""
        bmr = self.confirmed_bmr()
        bmr.action_start()
        step = bmr.step_ids[0]
        step.action_operator_sign()
        self._ipqc(step)
        form = Form(self.env['pharma.ipqc.result'])
        form.bmr_id = bmr
        form.step_id = step
        form.parameter_id = self.ipqc_spec.parameter_ids
        self.assertFalse(form.parameter_id)
        check = self.env['pharma.ipqc.result'].new({'bmr_id': bmr.id})
        check._onchange_parameter_id()
        self.assertEqual(check.expected_max, 0.0)

    def test_yield(self):
        """Low yield is flagged and needs the QA Director's sign-off."""
        bmr = self.confirmed_bmr()
        with self.assertRaises(ValidationError):
            bmr.write({'yield_actual': 20.0})
        with self.assertRaises(UserError):
            bmr.with_user(self.qa_user).action_qa_yield_signoff()
        bmr.yield_actual = 9.9
        self.assertFalse(bmr.yield_flag)
        with self.assertRaises(UserError):
            bmr.with_user(self.qa_user).action_qa_yield_signoff()
        bmr.yield_actual = 5.0
        self.assertTrue(bmr.yield_flag)
        with self.assertRaises(UserError):
            bmr.with_user(self.operator).action_qa_yield_signoff()
        bmr.with_user(self.qa_user).action_qa_yield_signoff()
        self.assertEqual(bmr.qa_yield_signed_by, self.qa_user)

    def _run_steps(self, bmr):
        """Sign every step of the BMR."""
        bmr.action_start()
        for step in bmr.step_ids:
            step.action_operator_sign()
            step.with_user(self.qa_user).action_supervisor_sign()

    def test_complete_bmr(self):
        """QA completes a BMR once its gates pass; the order is closed."""
        bmr = self.confirmed_bmr()
        with self.assertRaises(UserError):
            bmr.with_user(self.qa_user).action_complete()
        bmr.action_start()
        with self.assertRaises(UserError):
            bmr.with_user(self.operator).action_complete()
        with self.assertRaises(UserError):
            bmr.with_user(self.qa_user).action_complete()
        for step in bmr.step_ids:
            step.action_operator_sign()
            step.with_user(self.qa_user).action_supervisor_sign()
        self.assertTrue(bmr.all_steps_done)
        bmr.yield_actual = 5.0
        with self.assertRaises(UserError):
            bmr.with_user(self.qa_user).action_complete()
        bmr.with_user(self.qa_user).action_qa_yield_signoff()
        bmr.with_user(self.qa_user).sudo().action_complete()
        self.assertEqual(bmr.status, 'completed')
        self.assertEqual(bmr.production_id.state, 'done')
        self.assertTrue(bmr.production_id.pharma_bmr_completed)

    def test_complete_creates_finished_qc(self):
        """Completing a BMR with a finished lot raises the finished-goods QC order."""
        tracked = self.env['product.template'].create({
            'name': 'Tracked Tablets', 'is_storable': True, 'tracking': 'lot',
        })
        spec = self.create_spec(tracked, 'finished')
        spec.action_submit_review()
        spec.with_user(self.qa_user).action_approve()
        bom = self.create_bom(tracked, approve=True)
        mo = self.env['mrp.production'].create({
            'product_id': tracked.product_variant_id.id, 'bom_id': bom.id, 'product_qty': 1,
        })
        mo.action_confirm()
        mo.lot_producing_ids = self.create_lot(tracked.product_variant_id, 'FG-1')
        bmr = mo.bmr_ids
        bmr.yield_actual = 1.0
        self._run_steps(bmr)
        bmr.with_user(self.qa_user).sudo().action_complete()
        order = self.env['pharma.qc.test.order'].search([('lot_id', '=', mo.lot_producing_ids.id)])
        self.assertEqual(order.stage, 'finished')

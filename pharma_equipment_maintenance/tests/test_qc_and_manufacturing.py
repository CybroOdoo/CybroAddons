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
from odoo.exceptions import AccessError, RedirectWarning, UserError, ValidationError
from odoo.tests import Form, tagged

from .common import EquipmentCommon


@tagged('post_install', '-at_install')
class TestQcResults(EquipmentCommon):
    """The instrument behind each QC result."""

    lot_seq = 0

    def started_order(self, instrument=None):
        """A started test order whose Assay proposes ``instrument``."""
        if instrument:
            self.spec.parameter_ids.default_instrument_id = instrument
        type(self).lot_seq += 1
        order = self.create_order(lot=self.create_lot(name='LOT-EQ-%s' % self.lot_seq))
        order.action_start_test()
        return order

    def test_instrument_required(self):
        """A measured value names its instrument, proposed from the specification."""
        order = self.started_order()
        line = order.result_line_ids
        self.assertTrue(line.instrument_required)
        with self.assertRaises(ValidationError):
            line.write({'actual_value': 100.0})
        balance = self.fit_instrument()
        line.write({'instrument_id': balance.id, 'actual_value': 100.0})
        self.assertEqual((line.instrument_calibration_date, line.instrument_calibration_ok),
                         (self.days(0), True))
        proposed = self.started_order(balance).result_line_ids
        self.assertEqual(proposed.instrument_id, balance)
        form = Form(self.env['pharma.qc.test.order'])
        form.product_id = self.product_tmpl
        form.lot_id = self.create_lot(name='LOT-F')
        form.stage = 'incoming'
        form.spec_id = self.spec
        with form.result_line_ids.edit(0) as proposed_line:
            self.assertEqual(proposed_line.instrument_id, balance)

    def test_block(self):
        """Block mode refuses values from uncalibrated or unclean instruments."""
        balance = self.instrument()
        line = self.started_order(balance).result_line_ids
        with self.assertRaises(ValidationError):
            line.write({'actual_value': 100.0})
        self.calibrate(balance)
        with self.assertRaises(ValidationError):
            line.write({'actual_value': 100.0})
        self.clean(balance)
        line.write({'actual_value': 100.0})
        helper = self.instrument(name='Pipette')
        with self.assertRaises(ValidationError):
            line.write({'support_instrument_ids': [(6, 0, helper.ids)]})
        with Form(line.test_order_id) as form, form.result_line_ids.edit(0) as edit:
            edit.instrument_id = helper
            edit.instrument_id = balance

    def test_warn_and_approval(self):
        """Warn mode records the warning; block mode stops approval of an uncalibrated result."""
        self.set_check('warn')
        balance = self.instrument()
        order = self.started_order(balance)
        order.result_line_ids.write({'actual_value': 100.0})
        self.assertIn('was not clean', order.message_ids[0].body)
        self.assertFalse(order.result_line_ids.instrument_calibration_ok)
        self.set_check('block')
        with self.assertRaises(ValidationError):
            order.with_user(self.qa_user).action_approve()
        self.set_check('off')
        order.with_user(self.qa_user).action_approve()
        self.assertEqual(order.status, 'passed')

    def test_impact(self):
        """Results measured since the last passed calibration, and their batches."""
        balance = self.fit_instrument()
        order = self.started_order(balance)
        order.result_line_ids.write({'actual_value': 100.0})
        self.assertEqual(balance.impacted_result_count, 1)
        action = balance.action_calibration_impact_assessment()
        self.assertEqual(self.env['pharma.qc.result.line'].search(action['domain']), order.result_line_ids)
        batches = balance.action_view_impacted_batches()
        self.assertEqual(batches['domain'], [('id', 'in', order.lot_id.ids)])
        failed = self.calibration(balance, as_found=101.0, as_left=100.0)
        failed.action_complete()
        failed.with_user(self.qa_only).action_qa_verify()
        self.assertEqual(failed._impacted_results(), order.result_line_ids)
        self.assertIn('1 result(s) in 1 QC test(s)', failed.message_ids[0].body)


@tagged('post_install', '-at_install')
class TestManufacturingCheck(EquipmentCommon):
    """Equipment fitness when a manufacturing order is confirmed."""

    def test_block_and_override(self):
        """Unfit equipment blocks confirmation; QA may override with a justification."""
        machine = self.machine()
        mo = self.create_mo()
        self.assertEqual(mo._pharma_checked_equipment(), machine)
        with self.assertRaises(UserError):
            mo.with_user(self.operator).action_confirm()
        with self.assertRaises(RedirectWarning):
            mo.with_user(self.qa_only).action_confirm()
        with self.assertRaises(UserError):
            mo.write({'pharma_equipment_override_reason': 'Sneaky'})
        action = mo.with_user(self.qa_only).action_pharma_open_override()
        self.assertEqual(action['context'], {'default_production_id': mo.id})
        Wizard = self.env['pharma.equipment.override.wizard']
        wizard = Wizard.with_user(self.qa_only).create({'production_id': mo.id, 'justification': 'ok'})
        self.assertEqual(wizard.equipment_ids, machine)
        self.assertIn('not clean', wizard.issues_text)
        with self.assertRaises(AccessError):
            wizard.with_user(self.operator).action_confirm_override()
        with self.assertRaises(UserError):
            wizard.action_confirm_override()
        wizard.justification = 'Cleaning verified on paper; record entered late.'
        wizard.action_confirm_override()
        self.assertEqual((mo.state, mo.pharma_equipment_override_by), ('confirmed', self.qa_only))
        self.assertEqual(mo.pharma_equipment_ids, machine)
        self.assertEqual(mo.pharma_equipment_count, 1)
        self.assertIn('Equipment check overridden', ' '.join(mo.message_ids.mapped('body')))
        self.assertIn('under a QA override', machine.message_ids[0].body)
        self.assertFalse(mo._pharma_raise_override_deviation({}, 'x'))
        self.assertEqual(mo.action_view_pharma_equipment()['domain'], [('id', 'in', machine.ids)])
        with self.assertRaises(UserError):
            Wizard.with_user(self.qa_only).create({
                'production_id': mo.id, 'justification': 'Too late for this.'}).action_confirm_override()

    def test_fit_and_modes(self):
        """Fit equipment confirms; warn confirms with a notice; off does not check."""
        machine = self.machine()
        self.clean(machine)
        mo = self.create_mo()
        mo.action_confirm()
        self.assertEqual(mo.pharma_equipment_ids, machine)
        wizard = self.env['pharma.equipment.override.wizard'].with_user(self.qa_user).create(
            {'production_id': self.create_mo().id, 'justification': 'Nothing to override here.'})
        self.assertEqual(wizard.issues_text, 'All equipment is currently fit for use.')
        wizard.action_confirm_override()
        self.assertEqual(wizard.production_id.state, 'confirmed')
        machine._pharma_register_use(self.tablet)
        self.set_check('warn')
        warned = self.create_mo()
        notice = warned.action_confirm()
        self.assertEqual(notice['params']['title'], 'Confirmed with unfit equipment')
        self.assertIn('equipment check set to warn', warned.message_ids[0].body)
        self.set_check('off')
        self.assertTrue(self.create_mo().action_confirm())

    def test_sterile_product(self):
        """A sterile product also needs sterile equipment."""
        self.enable_sterile()
        self.cat_mfg.sudo().pharma_sterile = True
        machine = self.machine()
        self.clean(machine)
        self.tablet_tmpl.sudo().pharma_sterile_product = True
        mo = self.create_mo()
        self.assertTrue(mo._pharma_is_sterile_product())
        self.assertEqual(mo._pharma_equipment_issues(), {machine: ['not sterile']})

    def test_done_leaves_equipment_dirty(self):
        """A finished batch leaves its equipment dirty with the product."""
        machine = self.machine()
        self.clean(machine)
        mo = self.create_mo(qty=1.0)
        mo.action_confirm()
        mo.bmr_ids.sudo().write({'status': 'completed'})
        mo.qty_producing = 1.0
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')
        self.assertEqual((machine.cleaning_status, machine.last_product_id), ('dirty', self.tablet))

    def test_no_operations(self):
        """An order without work centres checks nothing."""
        self.machine()
        bom = self.env['mrp.bom'].create({'product_tmpl_id': self.tablet_tmpl.id, 'product_qty': 1})
        mo = self.create_mo(bom=bom)
        self.assertFalse(mo._pharma_checked_equipment())
        self.assertEqual(mo._pharma_issues_text({}), '')

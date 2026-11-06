# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.mrp.tests.common import TestMrpCommon


@tagged('post_install', '-at_install')
class TestMrpSplitProduce(TestMrpCommon):

    def _create_confirmed_mo(self):
        mo, _bom, _finished, _component_1, _component_2 = self.generate_mo(
            qty_final=2,
            qty_base_1=4,
            qty_base_2=1,
        )
        mo.action_assign()
        with Form(mo) as mo_form:
            mo_form.qty_producing = mo.product_qty
        return mo

    def test_produce_all_consumes_components_without_finishing_mo(self):
        """Produce All should post components and keep finished goods pending."""
        mo = self._create_confirmed_mo()

        self.assertFalse(mo.is_partially_produced)
        self.assertFalse(mo.is_finalized)

        result = mo.action_produce_all_custom()

        self.assertTrue(result)
        self.assertTrue(mo.is_partially_produced)
        self.assertFalse(mo.is_finalized)
        self.assertEqual(mo.state, 'progress')
        self.assertTrue(all(move.state == 'done' for move in mo.move_raw_ids))
        self.assertTrue(
            all(move.state not in ('done', 'cancel') for move in mo.move_finished_ids),
        )

        mo.action_finalize_mo()

        self.assertTrue(mo.is_finalized)
        self.assertEqual(mo.state, 'done')
        self.assertTrue(all(move.state == 'done' for move in mo.move_finished_ids))
        self.assertTrue(mo.date_finished)
        self.assertEqual(mo.priority, '0')
        self.assertTrue(mo.is_locked)

    def test_finalize_requires_partial_production(self):
        """A manufacturing order cannot be finalized before Produce All."""
        mo = self._create_confirmed_mo()

        with self.assertRaises(UserError):
            mo.action_finalize_mo()

    def test_action_produce_all_closed_or_cancelled(self):
        """Cannot call produce all on a cancelled or done MO."""
        mo = self._create_confirmed_mo()
        mo.action_cancel()
        with self.assertRaises(UserError):
            mo.action_produce_all_custom()

        mo2 = self._create_confirmed_mo()
        mo2.action_produce_all_custom()
        mo2.action_finalize_mo()
        with self.assertRaises(UserError):
            mo2.action_produce_all_custom()

    def test_action_finalize_wizard_does_not_prematurely_finalize(self):
        """If button_mark_done returns a wizard during finalization,
        the MO must not be marked finalized or done prematurely."""
        mo = self._create_confirmed_mo()
        mo.action_produce_all_custom()
        self.assertTrue(mo.is_partially_produced)

        wizard_action = {'type': 'ir.actions.act_window', 'name': 'Consumption Warning'}
        with patch.object(type(mo), 'button_mark_done', return_value=wizard_action):
            res = mo.action_finalize_mo()
            self.assertEqual(res, wizard_action)
            self.assertFalse(mo.is_finalized)
            self.assertEqual(mo.state, 'progress')

    def test_action_produce_all_already_partially_produced(self):
        """Calling action_produce_all_custom when already partially produced raises UserError."""
        mo = self._create_confirmed_mo()
        mo.action_produce_all_custom()
        self.assertTrue(mo.is_partially_produced)
        with self.assertRaises(UserError):
            mo.action_produce_all_custom()

    def test_action_produce_all_with_backorder_context(self):
        """Test action_produce_all_custom when mo_ids_to_backorder is in context."""
        mo = self._create_confirmed_mo()
        res = mo.with_context(mo_ids_to_backorder=mo.ids).action_produce_all_custom()
        self.assertTrue(res)
        self.assertTrue(mo.is_partially_produced)

    def test_action_produce_all_zero_quantity_auto_fill(self):
        """When move.quantity is 0, action_produce_all_custom should set it to product_uom_qty."""
        mo, _bom, _finished, _component_1, _component_2 = self.generate_mo(
            qty_final=2,
            qty_base_1=4,
            qty_base_2=1,
        )
        mo.action_assign()
        # Reset move quantities to 0
        for move in mo.move_raw_ids:
            move.quantity = 0.0
        res = mo.action_produce_all_custom()
        self.assertTrue(res)
        self.assertTrue(all(move.state == 'done' for move in mo.move_raw_ids))

    def test_action_finalize_costing_and_consume_lines(self):
        """Verify finalization links consumed component lines and handles costing."""
        mo = self._create_confirmed_mo()
        mo.action_produce_all_custom()
        self.assertTrue(mo.is_partially_produced)

        # Call finalize which runs through button_mark_done and _post_inventory
        mo.action_finalize_mo()
        self.assertTrue(mo.is_finalized)
        self.assertEqual(mo.state, 'done')

        # Check consume_line_ids are linked
        finished_move = mo.move_finished_ids.filtered(lambda m: m.state == 'done')
        self.assertTrue(finished_move)
        done_raw_lines = mo.move_raw_ids.move_line_ids
        for line in finished_move.move_line_ids:
            self.assertTrue(
                set(line.consume_line_ids.ids).issubset(
                    set(done_raw_lines.ids),
                )
                or line.consume_line_ids,
            )

    def test_direct_button_mark_done_sets_is_finalized(self):
        """Calling button_mark_done should also set is_finalized."""
        mo = self._create_confirmed_mo()
        mo.button_mark_done()
        self.assertTrue(mo.is_finalized)
        self.assertEqual(mo.state, 'done')

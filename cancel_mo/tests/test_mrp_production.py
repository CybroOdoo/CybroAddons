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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import Command
from odoo.addons.mrp.tests.common import TestMrpCommon
from odoo.exceptions import AccessError
from odoo.tests import Form, tagged


@tagged('post_install', '-at_install')
class TestMrpProductionCancel(TestMrpCommon):
    """Test cases for mrp.production model extensions in cancel_mo."""

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'].sudo().search([
            ('key', 'in', [
                'cancel_mo.is_cancel_inventory_moves',
                'cancel_mo.is_cancel_workorder',
            ])
        ]).unlink()

    def test_default_field_values_from_config(self):
        """Test default values on mrp.production based on ir.config_parameter."""
        # When parameters are absent
        mo, _, _, _, _ = self.generate_mo()
        self.assertFalse(mo.cancel_inventory_moves)
        self.assertFalse(mo.cancel_workorder)

        # When parameters are set to True
        self.env['ir.config_parameter'].sudo().set_str('cancel_mo.is_cancel_inventory_moves', 'True')
        self.env['ir.config_parameter'].sudo().set_str('cancel_mo.is_cancel_workorder', 'True')
        mo2, _, _, _, _ = self.generate_mo()
        self.assertTrue(mo2.cancel_inventory_moves)
        self.assertTrue(mo2.cancel_workorder)

        # When parameters are explicitly set to False
        self.env['ir.config_parameter'].sudo().set_str('cancel_mo.is_cancel_inventory_moves', 'False')
        self.env['ir.config_parameter'].sudo().set_str('cancel_mo.is_cancel_workorder', 'False')
        mo3, _, _, _, _ = self.generate_mo()
        self.assertFalse(mo3.cancel_inventory_moves)
        self.assertFalse(mo3.cancel_workorder)

    def test_action_cancel_mo_access_restriction(self):
        """Test that non-manager users cannot execute action_cancel_mo."""
        mo, _, _, p1, p2 = self.generate_mo()
        self.env['stock.quant']._update_available_quantity(p1, self.stock_location, 100)
        self.env['stock.quant']._update_available_quantity(p2, self.stock_location, 10)
        mo.action_assign()
        mo_form = Form(mo)
        mo_form.qty_producing = 5.0
        mo = mo_form.save()
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

        # mrp_user does not have mrp.group_mrp_manager
        with self.assertRaises(AccessError):
            mo.with_user(self.user_mrp_user).action_cancel_mo()

        # mrp_manager should be allowed
        mo.with_user(self.user_mrp_manager).action_cancel_mo()
        self.assertEqual(mo.state, 'cancel')

    def test_action_cancel_mo_non_done(self):
        """Test action_cancel_mo skips when MO is not in done state."""
        mo, _, _, _, _ = self.generate_mo()
        self.assertEqual(mo.state, 'confirmed')
        mo.with_user(self.user_mrp_manager).action_cancel_mo()
        # State remains confirmed because action_cancel_mo only acts on done MOs
        self.assertEqual(mo.state, 'confirmed')

    def test_action_cancel_mo_revert_inventory_and_valuation(self):
        """Test cancelling a done MO with cancel_inventory_moves=True reverses quants and creates unbuild."""
        mo, bom, p_final, p1, p2 = self.generate_mo(qty_final=5, qty_base_1=4, qty_base_2=1)
        self.env['stock.quant']._update_available_quantity(p1, self.stock_location, 100)
        self.env['stock.quant']._update_available_quantity(p2, self.stock_location, 10)
        mo.action_assign()

        mo_form = Form(mo)
        mo_form.qty_producing = 5.0
        mo = mo_form.save()
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

        # Stock before cancel: 5 finished goods, 80 p1 (100 - 5*4), 5 p2 (10 - 5*1)
        self.assertEqual(self.env['stock.quant']._get_available_quantity(p_final, self.stock_location), 5)
        self.assertEqual(self.env['stock.quant']._get_available_quantity(p1, self.stock_location), 80)
        self.assertEqual(self.env['stock.quant']._get_available_quantity(p2, self.stock_location), 5)

        mo.write({'cancel_inventory_moves': True, 'cancel_workorder': False})
        mo.with_user(self.user_mrp_manager).action_cancel_mo()

        self.assertEqual(mo.state, 'cancel', "MO should be cancelled")
        self.assertTrue(mo.unbuild_ids, "An unbuild order should be generated")
        self.assertEqual(mo.unbuild_ids.state, 'done', "The unbuild order should be done")

        # Stock after cancel: finished goods consumed, components returned
        self.assertEqual(self.env['stock.quant']._get_available_quantity(p_final, self.stock_location), 0)
        self.assertEqual(self.env['stock.quant']._get_available_quantity(p1, self.stock_location), 100)
        self.assertEqual(self.env['stock.quant']._get_available_quantity(p2, self.stock_location), 10)

    def test_action_cancel_mo_with_workorders(self):
        """Test cancelling a done MO with cancel_workorder=True cancels all work orders."""
        self.env.user.group_ids += self.group_mrp_routings
        bom = self.env['mrp.bom'].sudo().create({
            'product_id': self.product_4.id,
            'product_tmpl_id': self.product_4.product_tmpl_id.id,
            'uom_id': self.uom_unit.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({'product_id': self.product_2.id, 'product_qty': 2.0}),
            ],
            'operation_ids': [
                Command.create({
                    'name': 'Assembly Operation',
                    'workcenter_id': self.workcenter_1.id,
                    'time_cycle': 10,
                }),
            ],
        })
        mo_form = Form(self.env['mrp.production'])
        mo_form.bom_id = bom
        mo_form.product_qty = 2.0
        mo = mo_form.save()
        mo.action_confirm()
        self.assertTrue(mo.workorder_ids, "MO should have work orders")

        self.env['stock.quant']._update_available_quantity(self.product_2, self.stock_location, 10)
        mo.action_assign()
        mo.button_plan()
        mo.qty_producing = 2.0
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

        mo.write({'cancel_inventory_moves': False, 'cancel_workorder': True})
        mo.with_user(self.user_mrp_manager).action_cancel_mo()

        self.assertEqual(mo.state, 'cancel')
        self.assertTrue(all(wo.state == 'cancel' for wo in mo.workorder_ids), "All work orders should be cancelled")
        self.assertFalse(mo.unbuild_ids, "No unbuild order should be created when cancel_inventory_moves is False")

    def test_action_cancel_mo_both_options_disabled(self):
        """Test that when both options are False, neither inventory nor work orders are cancelled, but MO is cancelled."""
        mo, _, p_final, p1, p2 = self.generate_mo(qty_final=2, qty_base_1=1, qty_base_2=1)
        self.env['stock.quant']._update_available_quantity(p1, self.stock_location, 10)
        self.env['stock.quant']._update_available_quantity(p2, self.stock_location, 10)
        mo.action_assign()
        mo.qty_producing = 2.0
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

        mo.write({'cancel_inventory_moves': False, 'cancel_workorder': False})
        mo.with_user(self.user_mrp_manager).action_cancel_mo()

        self.assertEqual(mo.state, 'cancel', "MO should be cancelled")
        self.assertFalse(mo.unbuild_ids, "No unbuild order should be created when cancel_inventory_moves is False")
        # Finished goods should remain untouched
        self.assertEqual(self.env['stock.quant']._get_available_quantity(p_final, self.stock_location), 2)

    def test_action_cancel_override(self):
        """Test standard action_cancel delegation for both non-done and done MOs."""
        # Non-done MO (confirmed)
        mo_confirmed, _, _, _, _ = self.generate_mo()
        self.assertEqual(mo_confirmed.state, 'confirmed')
        mo_confirmed.with_user(self.user_mrp_manager).action_cancel()
        self.assertEqual(mo_confirmed.state, 'cancel')

        # Done MO
        mo_done, _, _, p1, p2 = self.generate_mo(qty_final=1, qty_base_1=1, qty_base_2=1)
        self.env['stock.quant']._update_available_quantity(p1, self.stock_location, 10)
        self.env['stock.quant']._update_available_quantity(p2, self.stock_location, 10)
        mo_done.action_assign()
        mo_done.qty_producing = 1.0
        mo_done.button_mark_done()
        self.assertEqual(mo_done.state, 'done')

        # action_cancel on done MO should invoke action_cancel_mo
        mo_done.write({'cancel_inventory_moves': True, 'cancel_workorder': False})
        mo_done.with_user(self.user_mrp_manager).action_cancel()
        self.assertEqual(mo_done.state, 'cancel')
        self.assertTrue(mo_done.unbuild_ids)

    def test_action_cancel_mo_both_options_enabled(self):
        """Test cancelling a done MO with both cancel_inventory_moves and cancel_workorder enabled."""
        self.env.user.group_ids += self.group_mrp_routings
        bom = self.env['mrp.bom'].sudo().create({
            'product_id': self.product_4.id,
            'product_tmpl_id': self.product_4.product_tmpl_id.id,
            'uom_id': self.uom_unit.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                Command.create({'product_id': self.product_2.id, 'product_qty': 2.0}),
            ],
            'operation_ids': [
                Command.create({
                    'name': 'Assembly Operation',
                    'workcenter_id': self.workcenter_1.id,
                    'time_cycle': 10,
                }),
            ],
        })
        mo_form = Form(self.env['mrp.production'])
        mo_form.bom_id = bom
        mo_form.product_qty = 2.0
        mo = mo_form.save()
        mo.action_confirm()

        self.env['stock.quant']._update_available_quantity(self.product_2, self.stock_location, 10)
        mo.action_assign()
        mo.button_plan()
        mo.qty_producing = 2.0
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

        mo.write({'cancel_inventory_moves': True, 'cancel_workorder': True})
        mo.with_user(self.user_mrp_manager).action_cancel_mo()

        self.assertEqual(mo.state, 'cancel')
        self.assertTrue(mo.unbuild_ids)
        self.assertEqual(mo.unbuild_ids.state, 'done')
        self.assertTrue(all(wo.state == 'cancel' for wo in mo.workorder_ids))
        self.assertEqual(self.env['stock.quant']._get_available_quantity(self.product_4, self.stock_location), 0)
        self.assertEqual(self.env['stock.quant']._get_available_quantity(self.product_2, self.stock_location), 10)

    def test_action_cancel_mo_with_tracking_lot(self):
        """Test cancelling a done MO producing tracked lot products passes lot_ids to unbuild."""
        mo, bom, p_final, p1, p2 = self.generate_mo(qty_final=5, tracking_final='lot')
        lot = self.env['stock.lot'].sudo().create({
            'name': 'LOT-TEST-001',
            'product_id': p_final.id,
            'company_id': self.env.company.id,
        })

        self.env['stock.quant']._update_available_quantity(p1, self.stock_location, 100)
        self.env['stock.quant']._update_available_quantity(p2, self.stock_location, 100)
        mo.action_assign()

        mo_form = Form(mo)
        mo_form.qty_producing = 5.0
        mo_form.lot_producing_ids.set(lot)
        mo = mo_form.save()
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')
        self.assertEqual(mo.lot_producing_ids, lot)

        mo.write({'cancel_inventory_moves': True, 'cancel_workorder': False})
        mo.with_user(self.user_mrp_manager).action_cancel_mo()

        self.assertEqual(mo.state, 'cancel')
        self.assertTrue(mo.unbuild_ids)
        self.assertEqual(mo.unbuild_ids.state, 'done')
        self.assertEqual(mo.unbuild_ids.lot_ids, lot)
        self.assertEqual(self.env['stock.quant']._get_available_quantity(p_final, self.stock_location, lot_id=lot), 0)

    def test_action_cancel_mo_zero_qty_produced(self):
        """Test that when qty_produced is 0 on done MO, unbuild is skipped."""
        mo, _, _, _, _ = self.generate_mo()
        mo.write({'state': 'done', 'qty_produced': 0.0, 'cancel_inventory_moves': True})
        mo.with_user(self.user_mrp_manager).action_cancel_mo()
        self.assertEqual(mo.state, 'cancel')
        self.assertFalse(mo.unbuild_ids, "Unbuild order must not be created when qty_produced is 0")

    def test_action_cancel_mo_open_moves(self):
        """Test that any leftover non-done moves on done MO are cancelled."""
        mo, _, _, p1, _ = self.generate_mo()
        mo.action_assign()
        mo_form = Form(mo)
        mo_form.qty_producing = 5.0
        mo = mo_form.save()
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

        extra_move = self.env['stock.move'].sudo().create({
            'product_id': p1.id,
            'product_uom_qty': 2.0,
            'uom_id': p1.uom_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': mo.location_dest_id.id,
            'raw_material_production_id': mo.id,
        })
        extra_move.write({'state': 'confirmed'})
        self.assertEqual(extra_move.state, 'confirmed')

        mo.write({'cancel_inventory_moves': False, 'cancel_workorder': False})
        mo.with_user(self.user_mrp_manager).action_cancel_mo()

        self.assertEqual(mo.state, 'cancel')
        self.assertEqual(extra_move.state, 'cancel', "Open moves linked to MO must be cancelled")

    def test_action_cancel_batch_mixed_states(self):
        """Test calling action_cancel on a recordset containing both confirmed and done MOs."""
        mo_confirmed, _, _, _, _ = self.generate_mo()
        self.assertEqual(mo_confirmed.state, 'confirmed')

        mo_done, _, _, p1, p2 = self.generate_mo(qty_final=1, qty_base_1=1, qty_base_2=1)
        self.env['stock.quant']._update_available_quantity(p1, self.stock_location, 10)
        self.env['stock.quant']._update_available_quantity(p2, self.stock_location, 10)
        mo_done.action_assign()
        mo_done.qty_producing = 1.0
        mo_done.button_mark_done()
        self.assertEqual(mo_done.state, 'done')
        mo_done.write({'cancel_inventory_moves': True, 'cancel_workorder': False})

        both_mos = mo_confirmed | mo_done
        both_mos.with_user(self.user_mrp_manager).action_cancel()

        self.assertEqual(mo_confirmed.state, 'cancel')
        self.assertEqual(mo_done.state, 'cancel')
        self.assertTrue(mo_done.unbuild_ids)

    def test_deprecated_action_cancel_wrapper(self):
        """Test _action_cancel executes without recursion on non-done and done MOs."""
        mo, _, _, _, _ = self.generate_mo()
        mo.with_user(self.user_mrp_manager)._action_cancel()
        self.assertEqual(mo.state, 'cancel')

    test_action_cancel_non_done_delegation = test_deprecated_action_cancel_wrapper

    def test_cancelled_state_recompute_persistence(self):
        """Test that cancelling a done MO persists in state='cancel' even when state is recomputed."""
        mo, _, _, p1, p2 = self.generate_mo(qty_final=2, qty_base_1=1, qty_base_2=1)
        self.env['stock.quant']._update_available_quantity(p1, self.stock_location, 10)
        self.env['stock.quant']._update_available_quantity(p2, self.stock_location, 10)
        mo.action_assign()
        mo.qty_producing = 2.0
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')
        self.assertTrue(all(m.state == 'done' for m in mo.move_raw_ids | mo.move_finished_ids))

        # Cancel the done MO
        mo.write({'cancel_inventory_moves': False, 'cancel_workorder': False})
        mo.with_user(self.user_mrp_manager).action_cancel_mo()
        self.assertEqual(mo.state, 'cancel')
        self.assertTrue(mo.is_cancelled)

        # Clear cache and trigger recomputation of state while moves remain done
        self.env.invalidate_all()
        mo._compute_state()
        self.assertEqual(mo.state, 'cancel', "Recomputing state must not revert cancelled done MO to 'done'")

        # Invalidate again and read state to verify DB stored value and cache
        self.env.invalidate_all()
        self.assertEqual(mo.state, 'cancel')

    def test_reset_cancelled_mo(self):
        """Test that resetting a cancelled MO clears is_cancelled flag."""
        mo, _, _, _, _ = self.generate_mo()
        mo.write({'state': 'cancel'})
        self.assertTrue(mo.is_cancelled)
        mo.action_reset_to_draft()
        self.assertFalse(mo.is_cancelled)
        self.assertEqual(mo.state, 'draft')

        # Test action_reset_to_progress clears is_cancelled
        mo.write({'state': 'cancel'})
        self.assertTrue(mo.is_cancelled)
        mo.action_reset_to_progress()
        self.assertFalse(mo.is_cancelled)
        self.assertEqual(mo.state, 'progress')

    def test_action_cancel_mo_open_pickings(self):
        """Test that non-done pickings associated with done MO are cancelled."""
        mo, _, _, p1, _ = self.generate_mo()
        mo_form = Form(mo)
        mo_form.qty_producing = 5.0
        mo = mo_form.save()
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

        if not mo.production_group_id:
            mo.production_group_id = self.env['procurement.group'].sudo().create({'name': mo.name})

        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': mo.picking_type_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.stock_location.id,
        })
        self.env['stock.move'].sudo().create({
            'product_id': p1.id,
            'product_uom_qty': 1.0,
            'uom_id': p1.uom_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.stock_location.id,
            'picking_id': picking.id,
            'production_group_id': mo.production_group_id.id,
        })
        picking.action_confirm()
        mo._compute_picking_ids()
        self.assertIn(picking, mo.picking_ids)
        self.assertIn(picking.state, ('draft', 'confirmed', 'assigned'))

        mo.with_user(self.user_mrp_manager).action_cancel_mo()
        self.assertEqual(mo.state, 'cancel')
        self.assertEqual(picking.state, 'cancel', "Open picking linked to MO must be cancelled")

    def test_deprecated_action_cancel_wrapper_done_mo(self):
        """Test _action_cancel delegates cleanly to action_cancel_mo for done MOs."""
        mo, _, _, p1, p2 = self.generate_mo(qty_final=1, qty_base_1=1, qty_base_2=1)
        self.env['stock.quant']._update_available_quantity(p1, self.stock_location, 10)
        self.env['stock.quant']._update_available_quantity(p2, self.stock_location, 10)
        mo.action_assign()
        mo.qty_producing = 1.0
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')

        mo.write({'cancel_inventory_moves': True, 'cancel_workorder': False})
        mo.with_user(self.user_mrp_manager)._action_cancel()
        self.assertEqual(mo.state, 'cancel')
        self.assertTrue(mo.unbuild_ids, "Unbuild order must be generated via _action_cancel on done MO")

    def test_deprecated_action_cancel_batch_mixed(self):
        """Test _action_cancel on a batch of both confirmed and done MOs without recursion."""
        mo_confirmed, _, _, _, _ = self.generate_mo()
        self.assertEqual(mo_confirmed.state, 'confirmed')

        mo_done, _, _, p1, p2 = self.generate_mo(qty_final=1, qty_base_1=1, qty_base_2=1)
        self.env['stock.quant']._update_available_quantity(p1, self.stock_location, 10)
        self.env['stock.quant']._update_available_quantity(p2, self.stock_location, 10)
        mo_done.action_assign()
        mo_done.qty_producing = 1.0
        mo_done.button_mark_done()
        self.assertEqual(mo_done.state, 'done')
        mo_done.write({'cancel_inventory_moves': True, 'cancel_workorder': False})

        both_mos = mo_confirmed | mo_done
        both_mos.with_user(self.user_mrp_manager)._action_cancel()

        self.assertEqual(mo_confirmed.state, 'cancel')
        self.assertEqual(mo_done.state, 'cancel')
        self.assertTrue(mo_done.unbuild_ids)

    def test_action_cancel_recursion_guard_active(self):
        """Test that invoking _action_cancel executes cleanly and cancels non-done MO."""
        mo, _, _, _, _ = self.generate_mo()
        res = mo.with_user(self.user_mrp_manager)._action_cancel()
        self.assertTrue(res)
        self.assertEqual(mo.state, 'cancel')

    def test_action_cancel_when_core_delegates_to_private_action_cancel(self):
        """Simulate core mrp action_cancel calling self._action_cancel() to verify no RecursionError."""
        mo, _, _, _, _ = self.generate_mo()
        self.assertEqual(mo.state, 'confirmed')

        from unittest.mock import patch
        from odoo.addons.mrp.models.mrp_production import MrpProduction as CoreMrpProduction
        orig_action_cancel = CoreMrpProduction.action_cancel

        def mock_core_action_cancel(rec):
            return rec._action_cancel()

        def mock_core_action_cancel_private(rec):
            return orig_action_cancel(rec)

        with patch.object(CoreMrpProduction, 'action_cancel', mock_core_action_cancel), \
             patch.object(CoreMrpProduction, '_action_cancel', mock_core_action_cancel_private, create=True):
            mo.with_user(self.user_mrp_manager).action_cancel()

        self.assertEqual(mo.state, 'cancel')

    def test_private_action_cancel_when_core_defines_it(self):
        """Simulate core mrp defining _action_cancel() to verify direct _action_cancel() calls."""
        mo, _, _, _, _ = self.generate_mo()
        self.assertEqual(mo.state, 'confirmed')

        from unittest.mock import patch
        from odoo.addons.mrp.models.mrp_production import MrpProduction as CoreMrpProduction
        orig_action_cancel = CoreMrpProduction.action_cancel

        def mock_core_action_cancel_private(rec):
            return orig_action_cancel(rec)

        with patch.object(CoreMrpProduction, '_action_cancel', mock_core_action_cancel_private, create=True):
            mo.with_user(self.user_mrp_manager)._action_cancel()

        self.assertEqual(mo.state, 'cancel')

    def test_write_state_transitions(self):
        """Test write method transitions update is_cancelled flag accurately."""
        mo, _, _, _, _ = self.generate_mo()
        # Normal field write doesn't affect is_cancelled
        mo.write({'priority': '1'})
        self.assertFalse(mo.is_cancelled)

        # Writing state='cancel' sets is_cancelled=True
        mo.write({'state': 'cancel'})
        self.assertTrue(mo.is_cancelled)

        # Writing another state sets is_cancelled=False
        mo.write({'state': 'confirmed'})
        self.assertFalse(mo.is_cancelled)


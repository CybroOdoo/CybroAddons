# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestCarWorkshop(TransactionCase):
    """Test cases for the main car.workshop model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Reuse an existing storable/service product to avoid cross-module
        # column constraints (e.g. sale_line_warn from the sale module)
        cls.service_product = cls.env['product.product'].search(
            [('type', '=', 'service')], limit=1)
        if not cls.service_product:
            cls.service_product = cls.env['product.product'].search([], limit=1)
        cls.material_product = cls.env['product.product'].search(
            [('type', '=', 'consu')], limit=1)
        if not cls.material_product:
            cls.material_product = cls.service_product

    def setUp(self):
        super().setUp()
        # Fleet vehicle
        self.brand = self.env['fleet.vehicle.model.brand'].create(
            {'name': 'Ford'})
        self.v_model = self.env['fleet.vehicle.model'].create({
            'name': 'Focus',
            'brand_id': self.brand.id,
        })
        self.fleet_vehicle = self.env['fleet.vehicle'].create(
            {'model_id': self.v_model.id})
        # Partner / Customer
        self.partner = self.env['res.partner'].create({'name': 'Jane Smith'})
        # Vehicle detail
        self.vehicle_detail = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
            'partner_id': self.partner.id,
        })
        # Stage
        self.stage = self.env['worksheet.stages'].create(
            {'name': 'Ready', 'sequence': 1, 'is_fold': False})
        self.done_stage = self.env['worksheet.stages'].create(
            {'name': 'Done', 'sequence': 99, 'is_fold': True})
        # Tag
        self.tag = self.env['worksheet.tag'].create(
            {'name': 'Express', 'color': 5})

    def _create_basic_workshop(self, name='Test Worksheet'):
        """Helper to create a basic car.workshop record."""
        return self.env['car.workshop'].create({
            'name': name,
            'vehicle_id': self.vehicle_detail.id,
            'stage_id': self.stage.id,
        })

    # -----------------------------------------------------------------------
    # CRUD Tests
    # -----------------------------------------------------------------------

    def test_create_workshop(self):
        """Test creating a car workshop record."""
        ws = self._create_basic_workshop()
        self.assertEqual(ws.name, 'Test Worksheet')
        self.assertEqual(ws.state, 'toinvoice',
                         "Default state should be 'toinvoice'.")
        self.assertEqual(ws.partner_id.id, self.partner.id,
                         "Partner should be auto-populated from vehicle.")


    def test_name_required(self):
        """Test that a name is required to create a worksheet."""
        self.assertTrue(self.env['car.workshop']._fields['name'].required)


    def test_update_workshop(self):
        """Test updating workshop fields."""
        ws = self._create_basic_workshop()
        ws.write({
            'name': 'Updated Worksheet',
            'priority': '1',
            'tag_ids': [(4, self.tag.id)],
        })
        self.assertEqual(ws.name, 'Updated Worksheet')
        self.assertEqual(ws.priority, '1')
        self.assertIn(self.tag, ws.tag_ids)


    def test_delete_workshop(self):
        """Test deleting a car workshop record."""
        ws = self._create_basic_workshop()
        ws_id = ws.id
        ws.unlink()
        self.assertFalse(
            self.env['car.workshop'].search([('id', '=', ws_id)]),
            "Workshop should be deleted.")


    # -----------------------------------------------------------------------
    # State / Button Tests
    # -----------------------------------------------------------------------




    def test_action_create_invoices_no_customer_raises(self):
        """Test that invoicing without a customer raises UserError."""
        vehicle_no_partner = self.env['vehicle.details'].create({
            'vehicle_id': self.fleet_vehicle.id,
        })
        ws = self.env['car.workshop'].create({
            'name': 'No Customer Worksheet',
            'vehicle_id': vehicle_no_partner.id,
            'stage_id': self.stage.id,
        })
        with self.assertRaises(UserError):
            ws.action_create_invoices()


    def test_action_create_invoices_no_planned_work_raises(self):
        """Test that invoicing with no planned work raises UserError."""
        ws = self._create_basic_workshop()
        with self.assertRaises(UserError):
            ws.action_create_invoices()


    # -----------------------------------------------------------------------
    # Computed Field Tests
    # -----------------------------------------------------------------------

    def test_compute_amount_total(self):
        """Test that amount_total is the sum of work costs + material prices."""
        ws = self._create_basic_workshop()
        self.env['planned.work'].create({
            'name': 'Test Work',
            'work_cost': 80.0,
            'work_id': ws.id,
        })
        self.env['material.used'].create({
            'material_product_id': self.material_product.id,
            'price': 20.0,
            'quantity': 1,
            'material_id': ws.id,
        })
        ws.invalidate_recordset()
        self.assertAlmostEqual(ws.amount_total, 100.0,
                               msg="Amount total should be 80 + 20 = 100.")


    def test_compute_effective_hour(self):
        """Test that effective_hour sums duration of completed works."""
        ws = self._create_basic_workshop()
        self.env['planned.work'].create({
            'name': 'Test Work',
            'time_spent': 3.0,
            'duration': 2.5,
            'is_completed': True,
            'work_id': ws.id,
        })
        ws.invalidate_recordset()
        self.assertAlmostEqual(ws.effective_hour, 2.5,
                               msg="Effective hour should equal the summed durations.")


    def test_compute_remaining_hour(self):
        """Test remaining_hour = total time_spent - effective_hour."""
        ws = self._create_basic_workshop()
        self.env['planned.work'].create({
            'name': 'Test Work',
            'time_spent': 5.0,
            'duration': 3.0,
            'is_completed': True,
            'work_id': ws.id,
        })
        ws.invalidate_recordset()
        # remaining = 5.0 (time_spent) - 3.0 (effective_hour)
        self.assertAlmostEqual(ws.remaining_hour, 2.0,
                               msg="Remaining hour should be 5.0 - 3.0 = 2.0.")


    def test_compute_invoice_count(self):
        """Test that invoice_count is initially 0 for a new worksheet."""
        ws = self._create_basic_workshop()
        self.assertEqual(ws.invoice_count, 0,
                         "Invoice count should be 0 for a new worksheet.")


    # -----------------------------------------------------------------------
    # Onchange Tests
    # -----------------------------------------------------------------------

    def test_onchange_vehicle_id(self):
        """Test that _onchange_vehicle_id correctly sets the partner_id."""
        ws = self.env['car.workshop'].new({
            'name': 'Onchange Test',
            'vehicle_id': self.vehicle_detail.id,
            'stage_id': self.stage.id,
        })
        ws._onchange_vehicle_id()
        self.assertEqual(ws.partner_id.id, self.vehicle_detail.partner_id.id,
                         "partner_id should be populated from vehicle's partner.")


    # -----------------------------------------------------------------------
    # Write / Stage Change Tests
    # -----------------------------------------------------------------------

    def test_write_stage_change_updates_date_last_stage_update(self):
        """Test that changing the stage updates date_last_stage_update."""
        ws = self._create_basic_workshop()
        old_date = ws.date_last_stage_update
        ws.write({'stage_id': self.done_stage.id})
        self.assertNotEqual(ws.date_last_stage_update, old_date,
                            "date_last_stage_update should change on stage change.")


    def test_write_stage_to_folded_sets_date_end(self):
        """Test that moving to a folded stage sets date_end."""
        ws = self._create_basic_workshop()
        self.assertFalse(ws.date_end,
                         "date_end should be False initially.")
        ws.write({'stage_id': self.done_stage.id})
        self.assertTrue(ws.date_end,
                        "date_end should be set when moving to a folded stage.")


    def test_write_stage_to_unfolded_clears_date_end(self):
        """Test that moving from folded back to unfolded clears date_end."""
        ws = self._create_basic_workshop()
        ws.write({'stage_id': self.done_stage.id})
        self.assertTrue(ws.date_end)
        ws.write({'stage_id': self.stage.id})
        self.assertFalse(ws.date_end,
                         "date_end should be cleared when moving to unfolded stage.")


    def test_write_kanban_state_resets_on_stage_change(self):
        """Test that kanban_state resets to 'normal' when stage changes."""
        ws = self._create_basic_workshop()
        ws.write({'kanban_state': 'blocked'})
        self.assertEqual(ws.kanban_state, 'blocked')
        ws.write({'stage_id': self.done_stage.id})
        self.assertEqual(ws.kanban_state, 'normal',
                         "kanban_state should reset to 'normal' on stage change.")


    # -----------------------------------------------------------------------
    # Action / Smart Button Tests
    # -----------------------------------------------------------------------

    def test_action_get_invoices(self):
        """Test that action_get_invoices returns a valid window action."""
        ws = self._create_basic_workshop()
        action = ws.action_get_invoices()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.move')


    def test_read_group_stage_ids(self):
        """Test that _read_group_stage_ids returns all stages."""
        all_stages = self.env['worksheet.stages'].search([])
        result = self.env['car.workshop']._read_group_stage_ids(
            all_stages, [])
        # Should contain at least our two created stages
        self.assertIn(self.stage, result)
        self.assertIn(self.done_stage, result)

    def test_compute_state(self):
        """Test that _compute_state properly updates state based on invoiced works."""
        ws = self._create_basic_workshop()
        self.assertEqual(ws.state, 'toinvoice')
        
        pw = self.env['planned.work'].create({
            'name': 'Test Work',
            'time_spent': 3.0,
            'is_completed': True,
            'work_id': ws.id,
        })
        ws.invalidate_recordset()
        self.assertEqual(ws.state, 'toinvoice')
        
        move = self.env['account.move'].create({'move_type': 'out_invoice'})
        line = self.env['account.move.line'].create({
            'move_id': move.id,
            'name': 'Test Work',
            'account_id': self.env['account.journal'].search([('type', '=', 'sale')], limit=1).default_account_id.id
        })
        pw.invoice_line_ids = [(4, line.id)]
        ws.invalidate_recordset()
        self.assertEqual(ws.state, 'invoiced')

    def test_process_demo_scheduler_queue(self):
        """Test the demo scheduler queue function runs without errors."""
        try:
            self.env['car.workshop'].process_demo_scheduler_queue()
        except Exception as e:
            self.fail(f"process_demo_scheduler_queue raised an exception: {e}")

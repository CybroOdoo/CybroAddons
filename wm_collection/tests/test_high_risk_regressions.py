"""Regression tests for the High-risk audit findings fixed in wm_collection:
BUG-001 (split reservations), BUG-015 (auto-sort UoM), BUG-016 (parent batch
closed early), BUG-017 (state guards), BUG-018 (route gate entries) and the
CO2 / valuation calculation fixes."""
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.wm_collection.models.waste_batch import wm_set_move_line_quantity


@tagged('post_install', '-at_install')
class TestHighRiskRegressions(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_approval', False)
        cls.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', False)
        cls.kg = cls.env.ref('uom.product_uom_kgm')
        cls.gram = cls.env.ref('uom.product_uom_gram')
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'High Risk Cat', 'code': 'HRC-REG', 'warm_factor_co2': 0.1})
        cls.category_b = cls.env['wm.waste.category'].create({
            'name': 'High Risk Cat B', 'code': 'HRC-REG-B', 'warm_factor_co2': 3.0})
        cls.product = cls.env['product.product'].create({
            'name': 'Reg Waste Product', 'is_waste_material': True, 'type': 'consu',
            'is_storable': True, 'tracking': 'lot', 'uom_id': cls.kg.id,
            'standard_price': 2.0, 'wm_waste_category_id': cls.category.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Regression Client'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Regression Site', 'partner_id': cls.partner.id})

    # ------------------------------------------------------------------ helpers
    def _batch(self, qty=100.0, uom=None, **vals):
        return self.env['waste.batch'].create(dict({
            'warehouse_id': self.warehouse.id,
            'location_id': self.location.id,
            'line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': qty,
                'uom_id': (uom or self.kg).id,
                'net_weight': qty,
            })],
        }, **vals))

    def _order(self, state='draft', lines=None):
        return self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'scheduled_start': '2026-09-25 08:00:00',
            'scheduled_end': '2026-09-25 10:00:00',
            'order_line_ids': lines or [(0, 0, {'category_id': self.category.id, 'weight': 50.0})],
            'state': state,
        })

    # ------------------------------------------------------------- BUG-001
    def test_bug_001_split_reservation_is_not_multiplied(self):
        lot1 = self.env['stock.lot'].create({'name': 'B1', 'product_id': self.product.id})
        lot2 = self.env['stock.lot'].create({'name': 'B2', 'product_id': self.product.id})
        Quant = self.env['stock.quant']
        Quant._update_available_quantity(self.product, self.location, 50.0, lot_id=lot1)
        Quant._update_available_quantity(self.product, self.location, 10.0, lot_id=lot2)
        dest = self.env['stock.location'].create({
            'name': 'Reg Dest', 'usage': 'internal',
            'location_id': self.warehouse.view_location_id.id})
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.int_type_id.id,
            'location_id': self.location.id, 'location_dest_id': dest.id})
        move = self.env['stock.move'].create({
            'product_id': self.product.id, 'product_uom': self.kg.id,
            'product_uom_qty': 60.0, 'location_id': self.location.id,
            'location_dest_id': dest.id, 'picking_id': picking.id})
        picking.action_confirm()
        picking.action_assign()
        self.assertGreater(len(move.move_line_ids), 1, "Reservation should span both lots")

        wm_set_move_line_quantity(move, 60.0, self.kg)
        self.assertAlmostEqual(sum(move.move_line_ids.mapped('quantity')), 60.0)

    def test_bug_001_explicit_lot_keeps_single_line(self):
        lot1 = self.env['stock.lot'].create({'name': 'C1', 'product_id': self.product.id})
        lot2 = self.env['stock.lot'].create({'name': 'C2', 'product_id': self.product.id})
        Quant = self.env['stock.quant']
        Quant._update_available_quantity(self.product, self.location, 50.0, lot_id=lot1)
        Quant._update_available_quantity(self.product, self.location, 10.0, lot_id=lot2)
        dest = self.env['stock.location'].create({
            'name': 'Reg Dest 2', 'usage': 'internal',
            'location_id': self.warehouse.view_location_id.id})
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.int_type_id.id,
            'location_id': self.location.id, 'location_dest_id': dest.id})
        move = self.env['stock.move'].create({
            'product_id': self.product.id, 'product_uom': self.kg.id,
            'product_uom_qty': 60.0, 'location_id': self.location.id,
            'location_dest_id': dest.id, 'picking_id': picking.id})
        picking.action_confirm()
        picking.action_assign()
        wm_set_move_line_quantity(move, 60.0, self.kg, lot1)
        self.assertEqual(len(move.move_line_ids), 1)
        self.assertAlmostEqual(move.move_line_ids.quantity, 60.0)

    # ------------------------------------------------------------- BUG-015
    def test_bug_015_auto_sort_moves_each_line_in_its_own_uom(self):
        batch = self._batch(qty=2000.0, uom=self.gram)
        captured = {}

        def fake_moves(self_, moves_data, origin=None):
            captured['data'] = moves_data
            return self_.env['stock.picking']

        with patch.object(type(batch), '_do_internal_moves_batch', fake_moves):
            batch._move_lines_to_location(
                batch.line_ids, self.location, origin='test')
        data = captured['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['uom'], self.gram)
        self.assertEqual(data[0]['qty'], 2000.0)
        self.assertEqual(data[0]['product'], self.product)

    # ------------------------------------------------------------- BUG-016
    def test_bug_016_parent_stays_open_while_unsorted_stock_remains(self):
        parent = self._batch(qty=100.0)
        parent.line_ids.write({'sorted_qty': 40.0})
        child = self._batch(qty=40.0, parent_batch_id=parent.id)
        parent.invalidate_recordset()
        self.assertTrue(parent.sorted_batch_ids)
        child.write({'status': 'disposed'})
        self.assertNotEqual(
            parent.status, 'disposed',
            "Parent must not close while 60 kg is still unsorted")
        # once everything is sorted the parent closes with its children
        parent.line_ids.write({'sorted_qty': 100.0})
        child.write({'status': 'disposed'})
        self.assertEqual(parent.status, 'disposed')

    # ------------------------------------------------------------- BUG-017
    def test_bug_017_completed_order_cannot_be_reprocessed(self):
        order = self._order(state='completed')
        for method in ('action_complete', 'action_dispatch', 'action_start', 'action_cancel'):
            with self.assertRaises(UserError, msg=method):
                getattr(order, method)()
        self.assertEqual(order.state, 'completed')

    def test_bug_017_missed_wizard_refuses_closed_orders(self):
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_missed_collection', 'True')
        order = self._order(state='completed')
        reason = self.env['wm.missed.reason'].create({'name': 'Reg reason'})
        wizard = self.env['wm.mark.missed.wizard'].create({
            'order_id': order.id, 'reason_id': reason.id})
        with self.assertRaises(UserError):
            wizard.action_confirm()
        self.assertFalse(order.retry_order_id)

    def test_bug_017_route_cannot_be_redispatched_or_recompleted(self):
        route = self.env['wm.route'].create({'date': fields.Date.today()})
        route.sudo().with_context(programmatic_state_change=True).write({'state': 'completed'})
        for method in ('action_dispatch_route', 'action_start_route', 'action_complete_route'):
            with self.assertRaises(UserError, msg=method):
                getattr(route, method)()

    # ------------------------------------------------------------- BUG-018
    def test_bug_018_itemised_rejection_only_is_partially_rejected(self):
        facility = self.env['wm.disposal.facility'].create({
            'name': 'Reg Facility', 'facility_type': 'treatment',
            'license_no': 'REG-1', 'company_id': self.env.company.id})
        order = self._order(state='completed')
        brand = self.env['fleet.vehicle.model.brand'].search([], limit=1) or \
            self.env['fleet.vehicle.model.brand'].create({'name': 'Reg Brand'})
        vehicle = self.env['fleet.vehicle'].create({
            'license_plate': 'REG-018',
            'model_id': self.env['fleet.vehicle.model'].create(
                {'name': 'Reg Model', 'brand_id': brand.id}).id})
        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': facility.id,
            'vehicle_id': vehicle.id,
            'collection_order_id': order.id,
            'confirmed_weight': 8000.0,
            'rejection_line_ids': [(0, 0, {
                'collection_point_id': self.point.id,
                'partner_id': self.partner.id,
                'rejected_weight': 2000.0,
                'rejection_reason': 'Contamination',
            })],
        })
        entry.action_process_reconciliation()
        self.assertEqual(entry.accepted_weight, 6000.0)
        self.assertEqual(entry.rejected_weight, 2000.0)
        self.assertEqual(entry.state, 'partially_rejected')

    # ------------------------------------------------------ calculations
    def test_co2_is_weighted_by_line_category(self):
        order = self._order(lines=[
            (0, 0, {'category_id': self.category.id, 'weight': 900.0}),
            (0, 0, {'category_id': self.category_b.id, 'weight': 100.0}),
        ])
        # (900 x 0.1 + 100 x 3.0) / 1000 = 0.39 (an unweighted average gave 1.55)
        self.assertAlmostEqual(order.co2_avoided_tons, 0.39, places=3)

    def test_valuation_qty_is_uom_aware_and_excludes_sorted_parent_stock(self):
        batch = self._batch(qty=2000.0, uom=self.gram)
        line = batch.line_ids
        # 2000 g of a kg-priced product is 2 kg (not 2000)
        self.assertAlmostEqual(line._get_valuation_qty(), 2.0)
        # a sorted parent is valued only for what is still unsorted
        batch.line_ids.write({'sorted_qty': 1500.0})
        self._batch(qty=1500.0, uom=self.gram, parent_batch_id=batch.id)
        batch.invalidate_recordset()
        self.assertAlmostEqual(line._get_valuation_qty(), 0.5)

    # ------------------------------------------------- inspection gate
    def test_inspection_gate_uses_only_the_latest_result(self):
        """A failed re-inspection overrides an earlier pass: the batch must not
        be receivable on the strength of the old pass."""
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', 'True')
        batch = self._batch()
        Inspection = self.env['wm.batch.inspection']
        self.assertFalse(batch._inspection_gate_passed(), "no inspection yet")
        Inspection.create({'batch_id': batch.id, 'state': 'passed',
                           'inspection_date': '2026-01-01 08:00:00'})
        self.assertTrue(batch._inspection_gate_passed())
        Inspection.create({'batch_id': batch.id, 'state': 'failed',
                           'inspection_date': '2026-02-01 08:00:00'})
        self.assertFalse(batch._inspection_gate_passed())
        with self.assertRaises(UserError):
            batch.action_receive_batch()
        Inspection.create({'batch_id': batch.id, 'state': 'passed',
                           'inspection_date': '2026-03-01 08:00:00'})
        self.assertTrue(batch._inspection_gate_passed())

    # ------------------------------------------------ Medium regressions
    def test_gate_entry_is_not_given_invented_weights(self):
        self.env['wm.disposal.facility'].create({
            'name': 'Auto Facility', 'facility_type': 'treatment',
            'license_no': 'AUTO-1', 'company_id': self.env.company.id})
        brand = self.env['fleet.vehicle.model.brand'].search([], limit=1) or \
            self.env['fleet.vehicle.model.brand'].create({'name': 'Auto Brand'})
        vehicle = self.env['fleet.vehicle'].create({
            'license_plate': 'AUTO-GATE',
            'model_id': self.env['fleet.vehicle.model'].create(
                {'name': 'Auto Model', 'brand_id': brand.id}).id})
        order = self._order(state='completed')
        order.write({'vehicle_id': vehicle.id})
        order._automate_gate_entry()
        entry = self.env['wm.facility.gate.entry'].search([('collection_order_id', '=', order.id)])
        self.assertTrue(entry)
        self.assertEqual(entry.accepted_weight, 0.0)

    def test_received_batch_quantity_cannot_be_edited_without_stock_move(self):
        batch = self._batch(qty=100.0)
        self.env.cr.execute("UPDATE waste_batch SET is_received = TRUE, status = 'received' WHERE id = %s", [batch.id])
        batch.invalidate_recordset()
        officer = self.env['res.users'].create({'name': 'Batch Editor', 'login': 'batch_editor_reg',
                                                'group_ids': [(6, 0, [
                                                    self.env.ref('base.group_user').id,
                                                    self.env.ref('wm_base.group_wm_inventory_operator').id])]})
        with self.assertRaises(UserError):
            batch.line_ids.with_user(officer).write({'quantity': 500.0})

    def test_free_container_is_not_invoiced_at_a_default_rate(self):
        container = self.env['wm.container'].search([], limit=1)
        if not container:
            self.skipTest("no container available")
        container.write({'rental_rate': 0.0, 'partner_id': self.partner.id})
        with self.assertRaises(UserError):
            container.action_create_rental_invoice()

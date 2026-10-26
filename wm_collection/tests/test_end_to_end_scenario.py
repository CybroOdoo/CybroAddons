"""One realistic day, end to end, with every number worked out by hand.

    Customer: 100 kg paper (2.00/kg) and 50 kg plastic (3.00/kg) collected on one route.

    collection   paper 100 + plastic 50                = 150 kg
    CO2          (100 x 0.5 + 50 x 2.0) / 1000          = 0.15 t   (category factors 0.5 and 2.0)
    scale        gross 3150 - tare 3000                = 150 kg net, all accepted
    stock        paper batch 100 kg, plastic batch 50 kg
    recycling    paper batch: 90 kg recovered as bales, 10 kg process loss
                 -> waste left in stock 0, bales 90, scrap 10 (nothing created or lost)
                 -> recovery 90 %, carbon abated 90 x 0.5 / 1000 = 0.045 t
    invoice      100 x 2.00 + 50 x 3.00                 = 350.00

Needs wm_collection, wm_compliance, wm_recycling and wm_contracts_billing
installed (the full suite does).
"""
import unittest
from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_collection', 'full_workflow')
class TestEndToEndScenario(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if 'wm.sla' not in cls.env:
            raise unittest.SkipTest("Needs the wm_contracts_billing module")
        env = cls.env
        # features that gate the flow are off, exactly as in the other workflow tests
        env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_approval', False)
        env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', False)

        cls.kg = env.ref('uom.product_uom_kgm')
        cls.cat_paper = env['wm.waste.category'].create({
            'name': 'E2E Paper', 'code': 'E2E-PAP', 'price': 2.0,
            'warm_factor_co2': 0.5, 'auto_create_batches_on_collection': True})
        cls.cat_plastic = env['wm.waste.category'].create({
            'name': 'E2E Plastic', 'code': 'E2E-PLA', 'price': 3.0,
            'warm_factor_co2': 2.0, 'auto_create_batches_on_collection': True})

        def waste_product(name, category):
            return env['product.product'].create({
                'name': name, 'is_waste_material': True, 'type': 'consu', 'is_storable': True,
                'uom_id': cls.kg.id, 'wm_waste_category_id': category.id, 'list_price': 0.0})
        cls.paper = waste_product('E2E Mixed Paper', cls.cat_paper)
        cls.plastic = waste_product('E2E Mixed Plastic', cls.cat_plastic)
        cls.bales = env['product.product'].create({
            'name': 'E2E Paper Bales', 'type': 'consu', 'is_storable': True, 'uom_id': cls.kg.id})

        cls.partner = env['res.partner'].create({'name': 'E2E Customer'})
        today = date.today()
        sla = env['wm.sla'].search([], limit=1) or env['wm.sla'].create({'name': 'E2E SLA'})
        cls.contract = env['wm.partner.contract'].create({
            'name': 'E2E-CONTRACT', 'partner_id': cls.partner.id, 'sla_id': sla.id,
            'frequency': 'monthly', 'no_of_frequency': 1,
            'from_date': today - timedelta(days=30), 'to_date': today + timedelta(days=335),
            'billing_basis': 'category_rate',
            'contract_line_ids': [
                (0, 0, {'category_id': cls.cat_paper.id, 'price': 2.0}),
                (0, 0, {'category_id': cls.cat_plastic.id, 'price': 3.0}),
            ],
        })
        cls.point = env['wm.collection.point'].create({
            'name': 'E2E Bay', 'partner_id': cls.partner.id})
        brand = env['fleet.vehicle.model.brand'].create({'name': 'E2E Brand'})
        model = env['fleet.vehicle.model'].create({'name': 'E2E Truck', 'brand_id': brand.id})
        cls.driver = env['res.partner'].create({'name': 'E2E Driver'})
        cls.vehicle = env['fleet.vehicle'].create({
            'model_id': model.id, 'driver_id': cls.driver.id, 'license_plate': 'E2E-001'})
        cls.route = env['wm.route'].create({
            'name': 'E2E Route', 'vehicle_id': cls.vehicle.id, 'driver_id': cls.driver.id,
            'line_ids': [(0, 0, {'collection_point_id': cls.point.id, 'sequence': 10})]})
        env['wm.vehicle.maintenance.checklist'].create({
            'name': 'E2E-PRE-TRIP', 'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip', 'state': 'checked'})
        cls.facility = env['wm.disposal.facility'].create({
            'name': 'E2E Plant', 'facility_type': 'recycling',
            'license_no': 'E2E-LIC', 'company_id': env.company.id})

    # ---------------------------------------------------------------- helpers
    def _stock(self, product, location):
        return sum(self.env['stock.quant'].search([
            ('product_id', '=', product.id), ('location_id', '=', location.id)]).mapped('quantity'))

    # ------------------------------------------------------------------ test
    def test_collection_to_invoice(self):
        env = self.env

        # 1. the order: estimates only, nothing weighed yet
        order = env['wm.collection.order'].create({
            'partner_id': self.partner.id, 'collection_point_id': self.point.id,
            'route_id': self.route.id, 'vehicle_id': self.vehicle.id,
            'driver_id': self.driver.id, 'contract_id': self.contract.id,
            'scheduled_start': fields.Datetime.now(),
            'order_line_ids': [
                (0, 0, {'category_id': self.cat_paper.id, 'product_id': self.paper.id,
                        'estimated_weight': 90.0, 'weight': 0.0}),
                (0, 0, {'category_id': self.cat_plastic.id, 'product_id': self.plastic.id,
                        'estimated_weight': 45.0, 'weight': 0.0}),
            ]})

        # 2. dispatch the route; it cannot be dispatched twice
        self.route.action_dispatch_route()
        self.assertEqual((self.route.state, order.state), ('dispatched', 'dispatched'))
        with self.assertRaises(UserError):
            self.route.action_dispatch_route()

        # 3. the driver weighs: 100 kg paper, 50 kg plastic; an unweighed order cannot complete
        with self.assertRaises(ValidationError, msg="zero weights cannot be completed"):
            order.action_complete()
        order.action_start()
        order.order_line_ids.filtered(lambda ln: ln.category_id == self.cat_paper).write({'weight': 100.0})
        order.order_line_ids.filtered(lambda ln: ln.category_id == self.cat_plastic).write({'weight': 50.0})
        order.action_complete()
        self.assertEqual(order.state, 'completed')
        self.assertAlmostEqual(order.confirmed_weight, 150.0)
        self.assertAlmostEqual(order.co2_avoided_tons, 0.15, places=4)
        with self.assertRaises(UserError, msg="completing twice must be refused"):
            order.action_complete()

        # 4. compliance: a manifest for the 150 kg exists and is on its way
        manifest = env['wm.compliance.manifest'].search([
            ('line_ids.collection_order_id', '=', order.id)])
        self.assertEqual(len(manifest), 1)
        self.assertAlmostEqual(manifest.total_quantity, 150.0)
        self.assertEqual(manifest.state, 'collected')

        # 5. the route completes and the waste is batched per category
        self.route.action_complete_route()
        self.assertEqual(self.route.state, 'completed')
        batches = env['waste.batch'].search([('route_id', '=', self.route.id)])
        self.assertEqual(len(batches), 2)
        paper_batch = batches.filtered(lambda b: b.category_id == self.cat_paper)
        plastic_batch = batches.filtered(lambda b: b.category_id == self.cat_plastic)
        self.assertAlmostEqual(paper_batch.intake_weight, 100.0)
        self.assertAlmostEqual(plastic_batch.intake_weight, 50.0)
        self.assertAlmostEqual(sum(paper_batch.line_ids.mapped('quantity')), 100.0)
        self.assertAlmostEqual(sum(plastic_batch.line_ids.mapped('quantity')), 50.0)

        # 6. the truck reaches the plant: the confirmed weight comes from the order, nothing is accepted yet
        gate = env['wm.facility.gate.entry'].search([('collection_order_id', '=', order.id)])
        self.assertEqual(len(gate), 1)
        self.assertEqual((gate.confirmed_weight, gate.accepted_weight), (150.0, 0.0))
        gate.action_process_reconciliation()
        self.assertEqual(gate.state, 'accepted')
        self.assertAlmostEqual(gate.accepted_weight, 150.0)
        self.assertEqual(manifest.state, 'disposed')
        self.assertEqual(
            env['waste.batch'].search_count([('collection_order_id', '=', order.id)]) +
            env['waste.batch'].search_count([('name', '=like', 'INTAKE/%s%%' % gate.name)]),
            2, "the scale must not create a second set of batches for the same waste")

        # 7. both batches go into stock, quantity for quantity
        for batch, product, qty in ((paper_batch, self.paper, 100.0), (plastic_batch, self.plastic, 50.0)):
            batch.action_receive_batch()
            batch.action_move_to_stock()
            self.assertTrue(batch.is_received)
            self.assertEqual(batch.status, 'received')
            self.assertAlmostEqual(self._stock(product, batch.location_id), qty)

        # 8. recycle the paper: 90 kg recovered as bales, 10 kg lost in the process
        out_loc = env['stock.location'].create({'name': 'E2E Bale Store', 'usage': 'internal'})
        stock_loc = paper_batch.location_id
        recycling = env['recycling.order'].create({
            'waste_batch_id': paper_batch.id,
            'line_ids': [(0, 0, {
                'product_id': self.bales.id, 'uom_id': self.kg.id,
                'dest_location_id': out_loc.id, 'expected_qty': 95.0, 'recovered_qty': 90.0})]})
        self.assertAlmostEqual(recycling.input_qty, 100.0)
        self.assertAlmostEqual(recycling.overall_recovery_rate, 90.0)
        self.assertAlmostEqual(recycling.line_ids.co2_avoided_tons, 0.045, places=4)
        recycling.action_confirm()
        recycling.action_start()
        recycling.action_done()
        self.assertEqual(recycling.state, 'done')
        self.assertEqual(paper_batch.status, 'recycled')
        scrap = recycling._get_scrap_location()
        self.assertAlmostEqual(self._stock(self.paper, stock_loc), 0.0, msg="all paper left the shelf")
        self.assertAlmostEqual(self._stock(self.bales, out_loc), 90.0)
        self.assertAlmostEqual(self._stock(self.paper, scrap), 10.0)
        self.assertAlmostEqual(
            self._stock(self.bales, out_loc) + self._stock(self.paper, scrap), 100.0,
            msg="nothing created or lost: 100 kg in = 90 recovered + 10 loss")
        self.assertAlmostEqual(self._stock(self.plastic, plastic_batch.location_id), 50.0,
                               msg="the other batch is untouched")
        # a finished recycling order is frozen: its recovered quantities cannot be rewritten
        with self.assertRaises(UserError):
            recycling.line_ids.write({'recovered_qty': 1.0})
        self.assertAlmostEqual(recycling.line_ids.recovered_qty, 90.0)
        self.assertEqual(recycling.state, 'done')

        # 9. month-end billing: 100 x 2.00 + 50 x 3.00 = 350.00, once
        today = date.today()
        run = env['wm.monthly.billing.run'].create({
            'name': 'E2E-RUN', 'partner_ids': [(6, 0, [self.partner.id])],
            'period_start': today - timedelta(days=5), 'period_end': today + timedelta(days=5)})
        run.action_run_billing()
        self.assertEqual(run.state, 'done')
        invoices = env['account.move'].search([('partner_id', '=', self.partner.id)])
        self.assertEqual(len(invoices), 1)
        self.assertAlmostEqual(invoices.amount_untaxed, 350.0)
        self.assertEqual(sorted(invoices.invoice_line_ids.mapped('price_subtotal')), [150.0, 200.0])
        self.assertEqual(order.billing_run_line_id.run_id, run)

        rerun = env['wm.monthly.billing.run'].create({
            'name': 'E2E-RERUN', 'partner_ids': [(6, 0, [self.partner.id])],
            'period_start': today - timedelta(days=5), 'period_end': today + timedelta(days=5)})
        rerun.action_run_billing()
        self.assertEqual(
            env['account.move'].search_count([('partner_id', '=', self.partner.id)]), 1,
            "an order already billed must not be billed again")

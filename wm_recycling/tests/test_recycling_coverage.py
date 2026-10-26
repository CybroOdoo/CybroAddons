"""Coverage tests: role checks, recovery constraints, unit conversion,
done/sale-order guards and smart-button actions of recycling orders."""
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_recycling')
class TestRecyclingCoverage(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_approval', False)
        cls.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', False)
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_kg = cls.env.ref('uom.product_uom_kgm')
        cls.uom_ton = cls.env.ref('uom.product_uom_ton')
        cls.warehouse = cls.env['stock.warehouse'].create({'name': 'Cov Recycling WH', 'code': 'CRWH'})
        cls.location = cls.warehouse.lot_stock_id
        cls.dest = cls.env['stock.location'].create({'name': 'Cov Output Bin', 'usage': 'internal'})
        cls.waste = cls.env['product.product'].create({
            'name': 'Cov Waste', 'is_waste_material': True, 'type': 'consu',
            'is_storable': True, 'uom_id': cls.uom_kg.id})
        cls.output = cls.env['product.product'].create({
            'name': 'Cov Output', 'type': 'consu', 'is_storable': True, 'uom_id': cls.uom_kg.id})
        cls.operator = new_test_user(cls.env, login='wm_cov_rec_op', groups='base.group_user,wm_base.group_wm_recycler')
        cls.outsider = new_test_user(cls.env, login='wm_cov_rec_out', groups='base.group_user')

    def _batch(self, qty=100.0):
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id, 'location_id': self.location.id,
            'line_ids': [(0, 0, {'product_id': self.waste.id, 'quantity': qty})]})
        batch.action_receive_batch()
        batch.action_move_to_stock()
        return batch

    def _order(self, qty=100.0, recovered=0.0, uom=None, price=0.0, with_line=True):
        order = self.env['recycling.order'].create({'waste_batch_id': self._batch(qty).id})
        if with_line:
            self.env['recycling.line'].create({
                'order_id': order.id, 'product_id': self.output.id,
                'uom_id': (uom or self.uom_kg).id, 'dest_location_id': self.dest.id,
                'expected_qty': qty, 'recovered_qty': recovered, 'sale_price': price})
        return order

    # ── Roles ───────────────────────────────────────────────────────────────
    def test_non_recycler_cannot_run_workflow(self):
        order = self._order()
        for method in ('action_confirm', 'action_start', 'action_done', 'action_cancel', 'action_reset_draft'):
            with self.subTest(method=method), self.assertRaises(UserError):
                getattr(order.with_user(self.outsider), method)()
        self.assertEqual(order.state, 'draft')

    def test_recycler_can_confirm(self):
        order = self._order()
        order.with_user(self.operator).action_confirm()
        self.assertEqual(order.state, 'confirmed')
        self.assertEqual(order.waste_batch_id.status, 'sorting')

    # ── Lines ───────────────────────────────────────────────────────────────
    def test_recovery_rate_and_line_value(self):
        order = self._order(qty=100.0, recovered=50.0, price=2.0)
        line = order.line_ids
        self.assertAlmostEqual(line.recovery_rate, 50.0)
        self.assertAlmostEqual(line.line_value, 100.0)
        line.expected_qty = 0.0
        self.assertEqual(line.recovery_rate, 0.0)

    def test_total_recovery_cannot_exceed_input(self):
        order = self._order(qty=100.0, recovered=60.0)
        with self.assertRaises(ValidationError):
            self.env['recycling.line'].create({
                'order_id': order.id, 'product_id': self.output.id, 'uom_id': self.uom_kg.id,
                'recovered_qty': 50.0})
        with self.assertRaises(ValidationError):
            order.line_ids.recovered_qty = 150.0

    def test_unit_conversion_in_totals_and_constraint(self):
        order = self._order(qty=1000.0, recovered=0.5, uom=self.uom_ton)
        line = order.line_ids
        self.assertAlmostEqual(line._recovered_qty_in(self.uom_kg), 500.0)
        self.assertAlmostEqual(line._recovered_qty_in(False), 0.5)
        self.assertAlmostEqual(order.total_recovered_qty, 500.0)
        self.assertAlmostEqual(order.overall_recovery_rate, 50.0)
        # 1.5 t > 1000 kg of input
        with self.assertRaises(ValidationError):
            line.recovered_qty = 1.5
        # not convertible: raw quantity is used
        self.assertAlmostEqual(line._recovered_qty_in(self.uom_unit), 0.5)

    def test_co2_avoided_uses_category_factor(self):
        order = self._order(qty=2000.0, recovered=1000.0)
        category = self.env['wm.waste.category'].create({'name': 'Cov CO2 Cat', 'code': 'COVCO2'})
        category.warm_factor_co2 = 2.0
        order.category_id = category
        self.assertAlmostEqual(order.line_ids.co2_avoided_tons, 2.0)
        self.assertAlmostEqual(order.co2_avoided_tons, 2.0)

    def test_line_onchange_product_prefills_uom_and_price(self):
        self.output.list_price = 7.5
        line = self.env['recycling.line'].new({'product_id': self.output.id})
        line._onchange_product_id()
        self.assertEqual(line.uom_id, self.output.uom_id)
        self.assertEqual(line.sale_price, 7.5)

    # ── action_done guards ──────────────────────────────────────────────────
    def test_done_requires_in_progress_and_recovered_qty(self):
        order = self._order(recovered=0.0)
        with self.assertRaises(UserError):
            order.action_done()
        order.action_confirm()
        with self.assertRaises(UserError):
            order.action_done()  # still only confirmed
        order.action_start()
        with self.assertRaises(UserError):
            order.action_done()  # zero recovered quantity
        self.assertEqual(order.state, 'in_progress')

    def test_start_requires_confirmed_and_confirm_requires_lines(self):
        order = self._order()
        with self.assertRaises(UserError):
            order.action_start()
        empty = self._order(with_line=False)
        with self.assertRaises(UserError):
            empty.action_confirm()

    def test_done_cannot_be_cancelled_and_reset_requires_cancelled(self):
        order = self._order(recovered=100.0)
        with self.assertRaises(UserError):
            order.action_reset_draft()
        order.action_confirm()
        order.action_start()
        order.action_done()
        self.assertEqual(order.state, 'done')
        self.assertEqual(order.waste_batch_id.status, 'recycled')
        self.assertTrue(order.date_done)
        self.assertTrue(order.line_ids.is_stocked)
        self.assertTrue(order.line_ids.is_consumed)
        with self.assertRaises(UserError):
            order.action_cancel()

    def test_cancel_and_reset_release_batch(self):
        order = self._order()
        order.action_confirm()
        order.action_cancel()
        self.assertEqual(order.waste_batch_id.status, 'received')
        order.action_reset_draft()
        self.assertEqual(order.state, 'draft')

    # ── Sale order / smart buttons ──────────────────────────────────────────
    def test_sale_order_requires_done_and_priced_lines(self):
        order = self._order(recovered=100.0, price=0.0)
        with self.assertRaises(UserError):
            order.action_create_sale_order()  # not done
        order.action_confirm()
        order.action_start()
        order.action_done()
        with self.assertRaises(UserError):
            order.action_create_sale_order()  # no priced line

    def test_sale_order_action_prefills_lines_and_reuses_existing(self):
        order = self._order(recovered=100.0, price=3.0)
        order.action_confirm()
        order.action_start()
        order.action_done()
        action = order.action_create_sale_order()
        self.assertEqual(action['res_model'], 'sale.order')
        self.assertEqual(action['context']['default_origin'], order.name)
        vals = action['context']['default_order_line'][0][2]
        self.assertEqual(vals['product_id'], self.output.id)
        self.assertEqual(vals['product_uom_qty'], 100.0)
        self.assertEqual(vals['price_unit'], 3.0)
        so = self.env['sale.order'].create({
            'partner_id': self.env['res.partner'].create({'name': 'Cov Buyer'}).id,
            'origin': order.name})
        order.invalidate_recordset(['sale_order_count'])
        self.assertEqual(order.sale_order_count, 1)
        again = order.action_create_sale_order()
        self.assertEqual(again['res_id'], so.id)
        views = order.action_view_sales()
        self.assertEqual(views['domain'], [('id', 'in', so.ids)])

    def test_batch_view_action_and_duplicate_guard(self):
        order = self._order()
        batch = order.waste_batch_id
        self.assertEqual(batch.recycling_order_count, 1)
        action = batch.action_view_recycling_orders()
        self.assertEqual(action['domain'], [('waste_batch_id', '=', batch.id)])
        with self.assertRaises(UserError):
            batch.action_create_recycling_order()
        order.action_confirm()
        order.action_cancel()
        self.assertEqual(batch.action_create_recycling_order()['res_model'], 'recycling.order')

    def test_unreceived_batch_cannot_create_order(self):
        batch = self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id, 'location_id': self.location.id,
            'line_ids': [(0, 0, {'product_id': self.waste.id, 'quantity': 5.0})]})
        with self.assertRaises(UserError):
            batch.action_create_recycling_order()

    def test_print_report_returns_report_action(self):
        order = self._order()
        action = order.action_print_report()
        self.assertTrue(action)
        self.assertIn(action['type'], ('ir.actions.report', 'ir.actions.act_window'))

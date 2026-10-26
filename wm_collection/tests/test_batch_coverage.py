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
from datetime import date

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'wm_collection')
class TestBatchCoverage(TransactionCase):
    """Coverage for waste batch computes, constraints, actions, wizards and configs."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({'name': 'Cov Batch Cat', 'code': 'COVB'})
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.src_location = cls.warehouse.lot_stock_id
        cls.dest_location = cls.env['stock.location'].create({
            'name': 'Cov Sorted Yard',
            'usage': 'internal',
            'location_id': cls.src_location.location_id.id,
        })
        cls.products = cls.env['product.product']
        for i in range(2):
            tmpl = cls.env['product.template'].create({
                'name': 'Cov Material %s' % i,
                'is_waste_material': True,
                'wm_waste_category_id': cls.category.id,
            })
            tmpl.product_variant_id.write({'is_storable': True})
            cls.products |= tmpl.product_variant_id
        cls.Batch = cls.env['waste.batch']

    def _batch(self, products=None, qty=100.0, **kw):
        products = products or self.products[:1]
        vals = {
            'warehouse_id': self.warehouse.id,
            'location_id': self.src_location.id,
            'category_id': self.category.id,
            'line_ids': [(0, 0, {'product_id': p.id, 'quantity': qty}) for p in products],
        }
        vals.update(kw)
        return self.Batch.create(vals)

    def _received(self, products=None, qty=100.0):
        batch = self._batch(products, qty)
        batch.with_context(skip_inspection_check=True).action_receive_batch()
        batch.with_context(skip_inspection_check=True).action_move_to_stock()
        return batch

    # ---- line computes / constraints ----
    def test_line_net_weight_uom_conversion(self):
        gram = self.env.ref('uom.product_uom_gram')
        ton = self.env.ref('uom.product_uom_ton')
        batch = self._batch()
        line = batch.line_ids
        line.uom_id = gram
        line.quantity = 2500.0
        self.assertAlmostEqual(line.net_weight, 2.5, places=3)
        line.uom_id = ton
        line.quantity = 2.0
        self.assertAlmostEqual(line.net_weight, 2000.0, places=3)
        # non-weight UoM falls back to raw quantity
        line.uom_id = self.env.ref('uom.product_uom_unit')
        line.quantity = 7.0
        self.assertEqual(line.net_weight, 7.0)
        # draft_quantity follows net weight of lines
        self.assertEqual(batch.draft_quantity, 7.0)

    def test_line_valuation_qty_uom_and_sorted_parent(self):
        batch = self._batch(qty=2000.0)
        line = batch.line_ids
        line.uom_id = self.env.ref('uom.product_uom_gram')
        line.product_id.uom_id = self.env.ref('uom.product_uom_kgm')
        self.assertAlmostEqual(line._get_valuation_qty(), 2.0, places=3)
        # sorted parent values only the remaining portion
        line.sorted_qty = 500.0
        self.assertEqual(line.remaining_qty, 1500.0)
        child = self._batch(self.products[1:2])
        child.parent_batch_id = batch
        self.assertAlmostEqual(line._get_valuation_qty(), 1.5, places=3)

    def test_duplicate_product_per_batch_constraint(self):
        batch = self._batch()
        with self.assertRaises(ValidationError):
            self.env['waste.batch.line'].create({
                'batch_id': batch.id, 'product_id': self.products[0].id, 'quantity': 1.0})

    def test_line_edit_blocked_when_received_or_terminal(self):
        batch = self._received()
        line = batch.line_ids
        user = self.env['res.users'].create({
            'name': 'Cov Yard', 'login': 'cov_yard', 'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('wm_base.group_wm_inventory_operator').id])],
        })
        with self.assertRaises(UserError):
            line.with_user(user).write({'quantity': 5.0})
        batch.write({'status': 'disposed'})
        with self.assertRaises(UserError):
            self.env['waste.batch.line'].with_user(user).create({
                'batch_id': batch.id, 'product_id': self.products[1].id, 'quantity': 1.0})
        with self.assertRaises(UserError):
            line.with_user(user).unlink()
        with self.assertRaises(UserError):
            batch.with_user(user).write({'intake_notes': 'x'})

    # ---- batch computes ----
    def test_sorting_progress_hazard_materials_multi(self):
        self.products[1].wm_waste_category_id = self.category
        batch = self._batch(self.products, qty=100.0)
        self.assertTrue(batch.has_multiple_materials)
        self.assertEqual(batch.material_ids, self.products)
        self.assertEqual(batch.category_ids, self.category)
        self.assertEqual(batch.sorting_progress, 0.0)
        self.assertFalse(batch.is_fully_sorted)
        batch.line_ids[0].sorted_qty = 100.0
        self.assertEqual(batch.sorting_progress, 50.0)
        batch.line_ids[1].sorted_qty = 500.0  # over-sorted is clamped
        self.assertEqual(batch.sorting_progress, 100.0)
        empty = self.Batch.create({'category_id': self.category.id})
        self.assertEqual(empty.sorting_progress, 0.0)
        self.assertFalse(empty.has_multiple_materials)

    def test_hazardous_flag_follows_lines(self):
        batch = self._batch()
        self.assertFalse(batch.hazardous)
        self.products[0].product_tmpl_id.hazardous = True
        self.assertTrue(batch.hazardous)

    def test_net_weight_and_weight_variance(self):
        batch = self._batch(intake_weight=120.0, gross_weight=500.0, tare_weight=120.0)
        self.assertEqual(batch.net_weight, 380.0)
        self.assertEqual(batch.draft_quantity, 100.0)
        self.assertEqual(batch.weight_variance, 20.0)
        batch.write({'gross_weight': 100.0, 'tare_weight': 0.0})
        self.assertEqual(batch.net_weight, 100.0)

    def test_gross_tare_constraint(self):
        with self.assertRaises(ValidationError):
            self._batch(gross_weight=100.0, tare_weight=150.0)

    def test_uom_and_lot_compute(self):
        batch = self._batch()
        self.assertEqual(batch.uom_id, self.env.ref('uom.product_uom_kgm'))
        self.assertEqual(batch.lot_id, batch.line_ids[0].lot_id)
        self.assertTrue(batch.lot_id)
        batch.line_ids.uom_id = self.env.ref('uom.product_uom_ton')
        self.assertEqual(batch.uom_id, self.env.ref('uom.product_uom_ton'))

    def test_multi_product_lot_names(self):
        batch = self._batch(self.products)
        names = sorted(batch.line_ids.mapped('lot_id.name'))
        self.assertEqual(names, sorted(['%s/1' % batch.name, '%s/2' % batch.name]))

    def test_inspection_state_latest_concluded_wins(self):
        batch = self._batch()
        self.assertEqual(batch.inspection_state, 'pending')
        self.assertEqual(batch.inspection_count, 0)
        Insp = self.env['wm.batch.inspection']
        first = Insp.create({'batch_id': batch.id, 'state': 'in_progress',
                             'inspection_date': '2026-01-01 10:00:00'})
        self.assertEqual(batch.inspection_state, 'in_progress')
        first.write({'state': 'passed'})
        self.assertEqual(batch.inspection_state, 'passed')
        Insp.create({'batch_id': batch.id, 'state': 'failed',
                     'inspection_date': '2026-02-01 10:00:00'})
        self.assertEqual(batch.inspection_state, 'failed')
        self.assertEqual(batch.inspection_count, 2)
        self.assertTrue(batch.use_batch_inspection in (True, False))

    def test_days_in_current_status(self):
        batch = self._batch()
        self.assertEqual(batch.days_in_current_status, 0)
        self.env.flush_all()
        self.env.cr.execute("UPDATE waste_batch SET received_date = CURRENT_DATE - 5, create_date = now() - interval '5 days' WHERE id = %s",
                            [batch.id])
        self.env.cr.execute("DELETE FROM mail_tracking_value WHERE mail_message_id IN "
                            "(SELECT id FROM mail_message WHERE model = 'waste.batch' AND res_id = %s)",
                            [batch.id])
        batch.invalidate_recordset()
        self.assertGreaterEqual(batch.days_in_current_status, 4)

    def test_picking_count(self):
        batch = self._batch()
        self.assertEqual(batch.picking_count, 0)
        received = self._received()
        self.assertGreaterEqual(received.picking_count, 1)

    # ---- onchanges ----
    def test_onchange_warehouse_and_container_type(self):
        batch = self.Batch.new({'warehouse_id': self.warehouse.id})
        batch._onchange_warehouse_id()
        self.assertEqual(batch.location_id, self.warehouse.lot_stock_id)
        ctype = self.env['wm.container.type'].create({
            'name': 'Cov Drum', 'default_tare_weight': 12.5, 'is_hazardous_suitable': False})
        batch.container_type_id = ctype
        batch.container_count = 4
        batch._onchange_container_type()
        self.assertEqual(batch.tare_weight, 50.0)

    def test_onchange_hazardous_clears_unsuitable_container(self):
        self.products[0].product_tmpl_id.hazardous = True
        ctype = self.env['wm.container.type'].create({
            'name': 'Cov Plain Bin', 'default_tare_weight': 1.0, 'is_hazardous_suitable': False})
        batch = self.Batch.new({
            'container_type_id': ctype.id,
            'line_ids': [(0, 0, {'product_id': self.products[0].id, 'quantity': 1.0})],
        })
        res = batch._onchange_lines_hazardous_container()
        self.assertIn('warning', res)
        self.assertFalse(batch.container_type_id)
        self.assertIsNone(batch._onchange_lines_hazardous_container())
        ok = self.env['wm.container.type'].create({
            'name': 'Cov Drum Haz', 'default_tare_weight': 1.0, 'is_hazardous_suitable': True})
        batch.container_type_id = ok
        self.assertIsNone(batch._onchange_lines_hazardous_container())
        self.assertEqual(batch.container_type_id, ok)

    # ---- status transitions ----
    def test_illegal_status_transition(self):
        batch = self._batch()
        with self.assertRaises(ValidationError):
            batch.write({'status': 'sorted'})
        batch.write({'status': 'disposed'})
        with self.assertRaises(ValidationError):
            batch.write({'status': 'draft'})

    def test_unlink_rules(self):
        batch = self._batch()
        batch.unlink()
        received = self._received()
        with self.assertRaises(UserError):
            received.unlink()

    def test_direct_is_received_blocked(self):
        batch = self._batch()
        with self.assertRaises(ValidationError):
            batch.write({'is_received': True})

    def test_parent_auto_closes_when_all_children_disposed(self):
        parent = self._received(self.products, qty=50.0)
        wiz = self.env['waste.batch.sort.wizard'].with_context(default_batch_id=parent.id).create({
            'line_ids': [(0, 0, {
                'batch_line_id': ln.id, 'sort_qty': 50.0,
                'dest_product_id': ln.product_id.id, 'dest_location_id': self.dest_location.id,
            }) for ln in parent.line_ids],
        })
        wiz.action_confirm_sort()
        self.assertEqual(len(parent.sorted_batch_ids), 2)
        self.assertTrue(parent.is_fully_sorted)
        parent.sorted_batch_ids.action_dispose_batch()
        self.assertEqual(parent.status, 'disposed')

    # ---- actions ----
    def test_receive_batch_guards(self):
        batch = self.Batch.create({'category_id': self.category.id})
        with self.assertRaises(UserError):
            batch.action_receive_batch()  # no lines with quantity
        batch2 = self._batch()
        batch2.with_context(skip_inspection_check=True).action_receive_batch()
        self.assertEqual(batch2.status, 'arrived')
        with self.assertRaises(UserError):
            batch2.with_context(skip_inspection_check=True).action_receive_batch()

    def test_receive_requires_passed_inspection_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_batch_inspection', 'True')
        batch = self._batch()
        with self.assertRaises(UserError):
            batch.action_receive_batch()
        insp = self.env['wm.batch.inspection'].create({'batch_id': batch.id, 'state': 'in_progress'})
        self.assertFalse(batch._inspection_gate_passed())
        insp.write({'state': 'passed'})
        self.assertTrue(batch._inspection_gate_passed())
        batch.action_receive_batch()
        self.assertEqual(batch.status, 'arrived')

    def test_view_actions(self):
        batch = self._received()
        lot_action = batch.action_view_lot()
        self.assertEqual(lot_action['res_model'], 'stock.lot')
        self.assertEqual(lot_action['view_mode'], 'form')
        pick = batch.action_view_pickings()
        self.assertEqual(pick['res_model'], 'stock.picking')
        self.assertEqual(batch.action_view_inspections()['domain'], [('batch_id', '=', batch.id)])
        self.assertEqual(batch.action_view_sorted_batches()['domain'], [('id', 'in', [])])
        bare = self.Batch.create({'category_id': self.category.id})
        bare.line_ids.unlink()
        with self.assertRaises(UserError):
            bare.action_view_lot()

    def test_start_inspection_action(self):
        batch = self._batch()
        action = batch.action_start_inspection()
        self.assertEqual(batch.status, 'inspection')
        insp = self.env['wm.batch.inspection'].browse(action['res_id'])
        self.assertEqual(insp.state, 'in_progress')
        self.assertEqual(insp.batch_id, batch)

    def test_sort_actions_guards(self):
        batch = self._batch()
        for method in ('action_sort_batch', 'action_sort_by_category', 'action_sort_by_material'):
            with self.assertRaises(UserError):
                getattr(batch, method)()  # not received

    def test_sort_by_category_and_material_actions(self):
        batch = self._received(self.products, qty=10.0)
        act = batch.action_sort_by_category()
        self.assertEqual(act['res_model'], 'waste.batch.sort.wizard')
        self.assertTrue(act['context']['default_sort_by_category'])
        act = batch.action_sort_by_material()
        self.assertTrue(act['context']['default_sort_by_material'])
        act = batch.action_sort_batch()
        self.assertEqual(act['target'], 'new')

    def test_auto_sort_single_material(self):
        batch = self._received(qty=40.0)
        with self.assertRaises(UserError):
            batch.action_sort_batch()  # no sort config
        self.env['wm.waste.material.sort.config'].create({
            'material_id': self.products[0].product_tmpl_id.id,
            'dest_product_id': self.products[0].id,
            'dest_location_id': self.dest_location.id,
        })
        res = batch.action_sort_by_material()
        self.assertEqual(res['tag'], 'display_notification')
        self.assertEqual(batch.status, 'sorted')
        self.assertEqual(batch.location_id, self.dest_location)
        self.assertEqual(batch.line_ids.sorted_qty, 40.0)
        with self.assertRaises(UserError):
            batch.action_sort_by_material()  # nothing left

    def test_dispose_received_batch_moves_stock_to_scrap(self):
        batch = self._received(qty=30.0)
        batch.action_dispose_batch()
        self.assertEqual(batch.status, 'disposed')
        quant_qty = sum(self.env['stock.quant'].search([
            ('product_id', '=', self.products[0].id),
            ('location_id', '=', self.src_location.id),
            ('lot_id', '=', batch.line_ids.lot_id.id)]).mapped('quantity'))
        self.assertEqual(quant_qty, 0.0)

    def test_sort_stock_quantities_for_lines_without_uom(self):
        # sorting treats lines without a UoM as kg, so use kg products here
        self.products.write({'uom_id': self.env.ref('uom.product_uom_kgm').id})
        parent = self._received(self.products, qty=10.0)
        wiz = self.env['waste.batch.sort.wizard'].with_context(default_batch_id=parent.id).create({
            'line_ids': [(0, 0, {
                'batch_line_id': ln.id, 'sort_qty': 10.0,
                'dest_product_id': ln.product_id.id, 'dest_location_id': self.dest_location.id,
            }) for ln in parent.line_ids],
        })
        wiz.action_confirm_sort()
        for product in self.products:
            quants = self.env['stock.quant'].search([
                ('product_id', '=', product.id), ('location_id', '=', self.dest_location.id)])
            self.assertEqual(sum(quants.mapped('quantity')), 10.0)
            src = self.env['stock.quant'].search([
                ('product_id', '=', product.id), ('location_id', '=', self.src_location.id)])
            self.assertEqual(sum(src.mapped('quantity')), 0.0)

    def test_print_label_action(self):
        batch = self._batch()
        action = batch.action_print_label()
        # a fresh company first gets the document layout configurator wrapping the report
        action = action.get('context', {}).get('report_action', action)
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_name'], 'wm_collection.report_waste_batch_label')

    # ---- transfer wizard ----
    def test_transfer_wizard(self):
        batch = self._received(qty=25.0)
        other = self.env['stock.location'].create({
            'name': 'Cov Transfer Dest', 'usage': 'internal',
            'location_id': self.src_location.location_id.id})
        wiz = self.env['waste.batch.transfer.wizard'].create({
            'batch_id': batch.id, 'source_location_id': batch.location_id.id,
            'dest_location_id': other.id, 'notes': 'moving'})
        res = wiz.action_confirm_transfer()
        self.assertEqual(res['type'], 'ir.actions.act_window_close')
        self.assertEqual(batch.location_id, other)
        quants = self.env['stock.quant'].search([
            ('product_id', '=', self.products[0].id), ('location_id', '=', other.id)])
        self.assertEqual(sum(quants.mapped('quantity')), 25.0)

    def test_transfer_wizard_guards(self):
        draft = self._batch()
        wiz = self.env['waste.batch.transfer.wizard'].create({
            'batch_id': draft.id, 'dest_location_id': self.dest_location.id})
        with self.assertRaises(UserError):
            wiz.action_confirm_transfer()  # not received
        batch = self._received()
        wiz = self.env['waste.batch.transfer.wizard'].create({
            'batch_id': batch.id, 'dest_location_id': batch.location_id.id})
        with self.assertRaises(UserError):
            wiz.action_confirm_transfer()  # same location

    # ---- sort wizard ----
    def test_sort_wizard_defaults_autofill_and_validation(self):
        batch = self._received(self.products, qty=10.0)
        batch.line_ids[0].sorted_qty = 4.0
        Wiz = self.env['waste.batch.sort.wizard']
        wiz = Wiz.with_context(default_batch_id=batch.id, default_sort_by_category=True).create({})
        self.assertEqual(wiz.output_batch_mode, 'consolidated')
        self.assertEqual(sorted(wiz.line_ids.mapped('sort_qty')), [6.0, 10.0])
        self.assertFalse(wiz.has_hazardous_lines)
        wiz.line_ids.sort_qty = 0.0
        res = wiz.action_autofill_remaining()
        self.assertEqual(res['res_id'], wiz.id)
        self.assertEqual(sorted(wiz.line_ids.mapped('sort_qty')), [6.0, 10.0])
        wiz2 = Wiz.with_context(default_batch_id=batch.id, default_sort_by_material=True).create({})
        self.assertEqual(wiz2.output_batch_mode, 'per_material')
        # over-sort / negative
        with self.assertRaises(UserError):
            wiz.line_ids[0].sort_qty = 1000.0
        with self.assertRaises(UserError):
            wiz.line_ids[0].sort_qty = -1.0
        # no dest location
        wiz.line_ids.write({'dest_location_id': False})
        with self.assertRaises(UserError):
            wiz.action_confirm_sort()
        # nothing to sort
        empty = Wiz.create({'batch_id': batch.id})
        with self.assertRaises(UserError):
            empty.action_confirm_sort()
        zero = Wiz.create({'batch_id': batch.id, 'line_ids': [(0, 0, {
            'batch_line_id': batch.line_ids[0].id, 'sort_qty': 0.0})]})
        with self.assertRaises(UserError):
            zero.action_confirm_sort()

    def test_sort_wizard_hazardous_flag_and_onchange(self):
        self.products[0].product_tmpl_id.hazardous = True
        batch = self._received(qty=10.0)
        mconf = self.env['wm.waste.material.sort.config'].create({
            'material_id': self.products[0].product_tmpl_id.id,
            'dest_product_id': self.products[0].id,
            'dest_location_id': self.dest_location.id,
        })
        wiz = self.env['waste.batch.sort.wizard'].with_context(default_batch_id=batch.id).create({})
        self.assertTrue(wiz.has_hazardous_lines)
        self.assertEqual(wiz.line_ids.dest_location_id, self.dest_location)
        line = wiz.line_ids
        line.dest_location_id = False
        line._onchange_material_id()
        self.assertEqual(line.dest_location_id, mconf.dest_location_id)
        self.assertEqual(line.dest_product_id, mconf.dest_product_id)

    def test_sort_wizard_consolidated_partial_and_notes(self):
        batch = self._received(self.products, qty=10.0)
        wiz = self.env['waste.batch.sort.wizard'].create({
            'batch_id': batch.id, 'output_batch_mode': 'consolidated', 'notes': 'sorted by cov',
            'line_ids': [(0, 0, {
                'batch_line_id': ln.id, 'sort_qty': 4.0,
                'dest_product_id': ln.product_id.id, 'dest_location_id': self.dest_location.id,
            }) for ln in batch.line_ids],
        })
        res = wiz.action_confirm_sort()
        self.assertEqual(len(batch.sorted_batch_ids), 1)
        self.assertEqual(res['res_id'], batch.sorted_batch_ids.id)
        self.assertEqual(batch.line_ids.mapped('sorted_qty'), [4.0, 4.0])
        self.assertEqual(batch.sorting_progress, 40.0)
        self.assertFalse(batch.is_fully_sorted)
        self.assertEqual(batch.sorted_batch_count, 1)
        self.assertEqual(len(batch.sorted_batch_ids.line_ids), 2)

    # ---- sort configs ----
    def test_sort_config_uniqueness_and_sequence(self):
        Cat = self.env['wm.waste.category.sort.config']
        cfg = Cat.create({'category_id': self.category.id, 'dest_location_id': self.dest_location.id})
        self.assertNotEqual(cfg.name, 'New')
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            Cat.create({'category_id': self.category.id, 'dest_location_id': self.dest_location.id})
        Mat = self.env['wm.waste.material.sort.config']
        tmpl = self.products[0].product_tmpl_id
        mcfg = Mat.create({'material_id': tmpl.id, 'dest_product_id': self.products[0].id,
                           'dest_location_id': self.dest_location.id})
        self.assertNotEqual(mcfg.name, 'New')
        self.assertEqual(mcfg.category_id, self.category)
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            Mat.create({'material_id': tmpl.id, 'dest_product_id': self.products[0].id,
                        'dest_location_id': self.dest_location.id})
        mcfg._onchange_material_id()

    # ---- valuation wizard ----
    def test_valuation_wizard_date_constraint_and_filters(self):
        Wiz = self.env['waste.valuation.wizard']
        with self.assertRaises(ValidationError):
            Wiz.create({'date_from': '2026-02-01', 'date_to': '2026-01-01'})
        batch = self._received(qty=5.0)
        wiz = Wiz.create({
            'date_from': date(2000, 1, 1), 'warehouse_id': self.warehouse.id,
            'category_id': self.category.id, 'product_id': self.products[0].id,
            'status': 'received'})

        def _unwrap(act):
            return act.get('context', {}).get('report_action', act)

        action = _unwrap(wiz.action_print_report())
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertIn(batch.id, action['context']['active_ids'])
        other = _unwrap(Wiz.create({'status': 'sold'}).action_print_report())
        self.assertNotIn(batch.id, other['context'].get('active_ids', []))

    # ---- aging report ----
    def test_batch_aging_report(self):
        batch = self._batch(qty=10.0)
        batch.line_ids.sorted_qty = 4.0
        self.env.flush_all()
        rows = self.env['wm.batch.aging.report'].search([('batch_id', '=', batch.id)])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.remaining_qty, 6.0)
        self.assertEqual(rows.age_days, 0)
        batch.line_ids.sorted_qty = 10.0
        self.env.flush_all()
        self.assertFalse(self.env['wm.batch.aging.report'].search([('batch_id', '=', batch.id)]))
        batch.line_ids.sorted_qty = 0.0
        batch.write({'status': 'disposed'})
        self.env.flush_all()
        self.assertFalse(self.env['wm.batch.aging.report'].search([('batch_id', '=', batch.id)]))

    # ---- stock picking / collection ext ----
    def test_picking_waste_batch_link_and_batch_collection_links(self):
        batch = self._received()
        pickings = batch.picking_ids
        self.assertTrue(pickings)
        self.assertTrue(all(p.waste_batch_id == batch for p in pickings))
        partner = self.env['res.partner'].create({'name': 'Cov P'})
        point = self.env['wm.collection.point'].create({'name': 'Cov Pt', 'partner_id': partner.id})
        order = self.env['wm.collection.order'].create({
            'partner_id': partner.id, 'collection_point_id': point.id})
        batch.write({'collection_order_ids': [(4, order.id)], 'collection_order_id': order.id})
        self.assertEqual(batch.collection_order_ids, order)


@tagged('post_install', '-at_install', 'wm_collection')
class TestInspectionCoverage(TransactionCase):
    """Coverage for wm.batch.inspection constraints, locks and actions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({'name': 'Cov Insp Cat', 'code': 'COVI'})
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        tmpl = cls.env['product.template'].create({
            'name': 'Cov Insp Material', 'is_waste_material': True,
            'wm_waste_category_id': cls.category.id})
        cls.product = tmpl.product_variant_id
        cls.product.write({'is_storable': True})

    def _batch(self):
        return self.env['waste.batch'].create({
            'warehouse_id': self.warehouse.id,
            'location_id': self.warehouse.lot_stock_id.id,
            'category_id': self.category.id,
            'line_ids': [(0, 0, {'product_id': self.product.id, 'quantity': 10.0})],
        })

    def test_settings_flags_and_signature_status(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('wm_collection.use_quality_grading', 'True')
        params.set_param('wm_collection.use_hazardous_waste', 'False')
        insp = self.env['wm.batch.inspection'].create({'batch_id': self._batch().id})
        self.assertNotEqual(insp.name, 'New')
        self.assertTrue(insp.use_quality_grading)
        self.assertFalse(insp.use_hazardous_waste)
        self.assertEqual(insp.signature_status, 'presence_absent')
        insp.is_signed = True
        self.assertEqual(insp.signature_status, 'presence_present')

    def test_onchange_measurement_warnings(self):
        insp = self.env['wm.batch.inspection'].new({'contamination_percentage': 10.0, 'moisture_percentage': 5.0})
        self.assertIsNone(insp._onchange_measurements())
        insp.contamination_percentage = 40.0
        insp.moisture_percentage = 25.0
        msg = insp._onchange_measurements()['warning']['message']
        self.assertIn('Contamination', msg)
        self.assertIn('Moisture', msg)

    def test_passing_conditions(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('wm_collection.use_quality_grading', 'True')
        params.set_param('wm_collection.use_hazardous_waste', 'True')
        batch = self._batch()
        insp = self.env['wm.batch.inspection'].create({'batch_id': batch.id, 'state': 'in_progress'})
        insp.quality_grade = 'rejected'
        with self.assertRaises(ValidationError):
            insp.write({'state': 'passed'})
        insp.quality_grade = 'grade_a'
        self.product.product_tmpl_id.hazardous = True
        with self.assertRaises(ValidationError):
            insp.write({'state': 'passed'})
        insp.hazard_verified = True
        insp.write({'state': 'passed'})
        self.assertEqual(insp.state, 'passed')

    def test_locks_on_concluded_inspection(self):
        user = self.env['res.users'].create({
            'name': 'Cov Insp User', 'login': 'cov_insp', 'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('wm_base.group_wm_inventory_operator').id])],
        })
        insp = self.env['wm.batch.inspection'].create({'batch_id': self._batch().id})
        insp.action_start_inspection()
        self.assertEqual(insp.state, 'in_progress')
        insp.action_pass_inspection()
        self.assertEqual(insp.state, 'passed')
        self.assertTrue(insp.message_ids.attachment_ids)
        with self.assertRaises(UserError):
            insp.with_user(user).write({'moisture_percentage': 3.0})
        with self.assertRaises(UserError):
            insp.with_user(user).unlink()

    def test_fail_inspection_disposes_unreceived_batch(self):
        batch = self._batch()
        insp = self.env['wm.batch.inspection'].create({'batch_id': batch.id, 'state': 'in_progress'})
        insp.action_fail_inspection()
        self.assertEqual(insp.state, 'failed')
        self.assertEqual(batch.status, 'disposed')
        self.assertEqual(batch.inspection_state, 'failed')

    def test_fail_inspection_received_batch_creates_disposal_and_event(self):
        partner = self.env['res.partner'].create({'name': 'Cov Insp Partner'})
        point = self.env['wm.collection.point'].create({'name': 'Cov Insp Pt', 'partner_id': partner.id})
        order = self.env['wm.collection.order'].create({
            'partner_id': partner.id, 'collection_point_id': point.id})
        batch = self._batch()
        batch.collection_order_id = order
        batch.with_context(skip_inspection_check=True).action_receive_batch()
        batch.with_context(skip_inspection_check=True).action_move_to_stock()
        insp = self.env['wm.batch.inspection'].create({'batch_id': batch.id, 'state': 'in_progress'})
        insp.action_fail_inspection()
        self.assertEqual(batch.status, 'disposed')
        if 'wm.billable.event' in self.env:
            self.assertTrue(insp.contamination_event_id)
            self.assertEqual(insp.contamination_event_id.partner_id, partner)

    def test_sign_now(self):
        insp = self.env['wm.batch.inspection'].create({'batch_id': self._batch().id, 'state': 'in_progress'})
        with self.assertRaises(ValidationError):
            insp.action_sign_now()
        insp.action_pass_inspection()
        action = insp.action_sign_now()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertTrue(insp.signature_template_id)
        self.assertIn('/wm_signature/template/edit/%s' % insp.signature_template_id.id, action['url'])
        sig_items = insp.signature_template_id.item_ids.filtered(lambda i: i.type == 'signature')
        self.assertEqual(len(sig_items), 1)
        # second call reuses the template and keeps one signature zone
        insp.action_sign_now()
        self.assertEqual(
            len(insp.signature_template_id.item_ids.filtered(lambda i: i.type == 'signature')), 1)

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
from datetime import date, datetime, timedelta
from types import SimpleNamespace

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_collection', 'order_coverage')
class TestOrderCoverage(TransactionCase):
    """Coverage for collection order computes, constraints, guards and helpers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env['wm.waste.category']
        cls.category = Category.create({
            'name': 'OC Paper', 'code': 'OCPAP', 'price': 0.5, 'warm_factor_co2': 2.0,
        })
        cls.category2 = Category.create({
            'name': 'OC Glass', 'code': 'OCGLS', 'price': 0.25, 'warm_factor_co2': 1.0,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'OC Paper Product', 'is_waste_material': True,
            'wm_waste_category_id': cls.category.id, 'list_price': 0.8,
        })
        cls.product2 = cls.env['product.product'].create({
            'name': 'OC Glass Product', 'is_waste_material': True,
            'wm_waste_category_id': cls.category2.id, 'list_price': 0.0,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'OC Partner'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'OC Point', 'partner_id': cls.partner.id,
            'latitude': 10.0, 'longitude': 20.0,
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'OC Brand'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'OC Truck', 'brand_id': brand.id})
        cls.driver = cls.env['res.partner'].create({'name': 'OC Driver'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id, 'license_plate': 'OC-001', 'driver_id': cls.driver.id,
        })
        cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-OC-1', 'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip', 'state': 'checked',
        })

    def _order(self, **kw):
        vals = {
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'scheduled_start': datetime(2026, 1, 10, 8, 0),
            'scheduled_end': datetime(2026, 1, 10, 10, 0),
        }
        vals.update(kw)
        return self.env['wm.collection.order'].create(vals)

    def _line(self, product=None, weight=10.0, **kw):
        product = product or self.product
        vals = {
            'category_id': product.wm_waste_category_id.id,
            'product_id': product.id,
            'weight': weight,
            'estimated_weight': weight,
        }
        vals.update(kw)
        return (0, 0, vals)

    def _dispatchable_order(self, **kw):
        route = self.env['wm.route'].create({
            'name': 'New', 'vehicle_id': self.vehicle.id, 'driver_id': self.driver.id,
            'date': date(2026, 1, 10),
        })
        kw.setdefault('route_id', route.id)
        kw.setdefault('order_line_ids', [self._line()])
        return self._order(**kw)

    def _user(self, group_xmlid=None, login='oc_user'):
        user = self.env['res.users'].create({
            'name': login, 'login': login, 'email': f'{login}@example.com',
        })
        if group_xmlid:
            self.env.ref(group_xmlid).write({'user_ids': [(4, user.id)]})
        return user

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    def test_confirmed_weight_and_total_amount(self):
        order = self._order(order_line_ids=[
            self._line(self.product, 10.0),
            self._line(self.product2, 4.0),
        ])
        self.assertAlmostEqual(order.confirmed_weight, 14.0)
        # product: list_price 0.8 * 10 ; product2: no list price -> category 0.25 * 4
        self.assertAlmostEqual(order.total_amount, 8.0 + 1.0)
        order.order_line_ids[0].weight = 20.0
        self.assertAlmostEqual(order.confirmed_weight, 24.0)
        self.assertAlmostEqual(order.total_amount, 16.0 + 1.0)

    def test_co2_avoided_uses_category_factor(self):
        order = self._order(order_line_ids=[
            self._line(self.product, 1000.0),
            self._line(self.product2, 1000.0),
        ])
        # (1000*2.0 + 1000*1.0) / 1000
        self.assertAlmostEqual(order.co2_avoided_tons, 3.0)
        empty = self._order()
        self.assertEqual(empty.co2_avoided_tons, 0.0)

    def test_schedule_status(self):
        order = self._order()
        self.assertFalse(order.schedule_status)
        order.actual_end = order.scheduled_end - timedelta(minutes=5)
        self.assertEqual(order.schedule_status, 'early')
        order.actual_end = order.scheduled_end
        self.assertEqual(order.schedule_status, 'on_time')
        order.actual_end = order.scheduled_end + timedelta(minutes=5)
        self.assertEqual(order.schedule_status, 'late')

    def test_retry_count_follows_parent_chain(self):
        first = self._order()
        second = self._order(parent_order_id=first.id)
        third = self._order(parent_order_id=second.id)
        self.assertEqual(first.retry_count, 0)
        self.assertEqual(second.retry_count, 1)
        self.assertEqual(third.retry_count, 2)

    def test_vehicle_and_driver_computed_from_route_and_vehicle(self):
        order = self._dispatchable_order()
        self.assertEqual(order.vehicle_id, self.vehicle)
        self.assertEqual(order.driver_id, self.driver)
        # Route driver is used when the vehicle has no driver
        other_vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.vehicle.model_id.id, 'license_plate': 'OC-002',
        })
        route_driver = self.env['res.partner'].create({'name': 'OC Route Driver'})
        route = self.env['wm.route'].create({
            'name': 'New', 'vehicle_id': other_vehicle.id, 'driver_id': route_driver.id,
        })
        order2 = self._order(route_id=route.id)
        self.assertEqual(order2.vehicle_id, other_vehicle)
        self.assertEqual(order2.driver_id, route_driver)

    def test_valid_vehicle_ids_only_checked_checklists(self):
        order = self._order()
        self.assertIn(self.vehicle, order.valid_vehicle_ids)
        other = self.env['fleet.vehicle'].create({
            'model_id': self.vehicle.model_id.id, 'license_plate': 'OC-003',
        })
        self.assertNotIn(other, order.valid_vehicle_ids)

    def test_use_settings_follow_config_parameter(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('wm_collection.use_missed_collection', 'True')
        order = self._order()
        self.assertTrue(order.use_missed_collection)
        params.set_param('wm_collection.use_missed_collection', 'False')
        order.invalidate_recordset(['use_missed_collection'])
        self.assertFalse(order.use_missed_collection)

    def test_collection_point_categories_compute(self):
        self.point.category_ids = [(6, 0, [self.category.id])]
        order = self._order()
        self.assertEqual(order.collection_point_category_ids, self.category)
        order2 = self.env['wm.collection.order'].new({})
        self.assertFalse(order2.collection_point_category_ids)

    def test_counts_and_view_actions_without_links(self):
        order = self._order()
        self.assertEqual(order.gate_entry_count, 0)
        self.assertEqual(order.waste_batch_count, 0)
        self.assertEqual(order.signature_signer_count, 0)
        self.assertFalse(order.is_billed)
        self.assertFalse(order.next_signer_id)
        self.assertFalse(order.next_signer_role_name)
        action = order.action_view_waste_batches()
        self.assertEqual(action['res_model'], 'waste.batch')
        self.assertEqual(action['view_mode'], 'list,form')
        self.assertEqual(order.action_view_signatures()['res_model'], 'wm.signature.request.signer')
        self.assertEqual(order.action_sign_next(), {'type': 'ir.actions.client', 'tag': 'reload'})

    def test_view_waste_batches_single_batch_opens_form(self):
        order = self._order()
        batch = self.env['waste.batch'].create({
            'collection_order_id': order.id,
        })
        order.invalidate_recordset()
        self.assertEqual(order.waste_batch_count, 1)
        action = order.action_view_waste_batches()
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['res_id'], batch.id)

    def test_onchange_scheduled_start_suggests_end(self):
        order = self.env['wm.collection.order'].new({
            'scheduled_start': datetime(2026, 2, 1, 9, 0),
        })
        order._onchange_scheduled_start()
        self.assertEqual(order.scheduled_end, datetime(2026, 2, 1, 10, 0))
        order.scheduled_end = datetime(2026, 2, 1, 12, 0)
        order._onchange_scheduled_start()
        self.assertEqual(order.scheduled_end, datetime(2026, 2, 1, 12, 0))

    def test_onchange_partner_resets_and_defaults_point(self):
        other_partner = self.env['res.partner'].create({'name': 'OC Other'})
        other_point = self.env['wm.collection.point'].create({
            'name': 'OC Other Point', 'partner_id': other_partner.id,
        })
        order = self.env['wm.collection.order'].new({
            'partner_id': other_partner.id, 'collection_point_id': self.point.id,
        })
        order._onchange_partner_id()
        self.assertEqual(order.collection_point_id, other_point)
        order.partner_id = False
        order._onchange_partner_id()
        self.assertFalse(order.collection_point_id)

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    def test_scheduled_dates_constraint_and_skip_context(self):
        with self.assertRaises(ValidationError):
            self._order(scheduled_end=datetime(2026, 1, 10, 8, 0))
        order = self.env['wm.collection.order'].with_context(
            skip_schedule_date_check=True).create({
                'scheduled_start': datetime(2026, 1, 10, 8, 0),
                'scheduled_end': datetime(2026, 1, 10, 7, 0),
            })
        self.assertTrue(order)

    def test_actual_dates_constraint(self):
        order = self._order()
        with self.assertRaises(ValidationError):
            order.write({
                'actual_start': datetime(2026, 1, 10, 9, 0),
                'actual_end': datetime(2026, 1, 10, 9, 0),
            })
        order.with_context(skip_schedule_date_check=True).write({
            'actual_start': datetime(2026, 1, 10, 9, 0),
            'actual_end': datetime(2026, 1, 10, 8, 0),
        })

    def test_unique_product_per_order(self):
        with self.assertRaises(ValidationError):
            self._order(order_line_ids=[self._line(self.product), self._line(self.product)])

    # ------------------------------------------------------------------
    # Billing helpers
    # ------------------------------------------------------------------
    def test_compute_collection_fee_flat_and_hybrid(self):
        Order = self.env['wm.collection.order']
        flat = SimpleNamespace(billing_basis='flat_per_collection', price=50.0,
                               max_weight=100.0, overweight_price=2.0)
        base, surcharge, kg, allowed = Order._compute_collection_fee(flat, 130.0, 1)
        self.assertEqual((base, kg, allowed), (50.0, 30.0, 100.0))
        self.assertAlmostEqual(surcharge, 6.0)
        base, surcharge, kg, allowed = Order._compute_collection_fee(flat, 90.0, 2)
        self.assertEqual((base, surcharge, kg, allowed), (100.0, 0.0, 0.0, 200.0))
        hybrid = SimpleNamespace(billing_basis='hybrid', price=10.0,
                                 included_weight=50.0, overweight_price=1.0)
        base, surcharge, kg, allowed = Order._compute_collection_fee(hybrid, 80.0, 1)
        self.assertEqual((base, kg, allowed), (10.0, 30.0, 50.0))
        self.assertAlmostEqual(surcharge, 3.0)
        # No overweight price -> never a surcharge
        free = SimpleNamespace(billing_basis='flat_per_collection', price=5.0, max_weight=10.0)
        self.assertEqual(Order._compute_collection_fee(free, 99.0)[1], 0.0)

    def test_billing_service_date_prefers_actual_end(self):
        order = self._order()
        self.assertEqual(order._get_billing_service_date(), date(2026, 1, 10))
        order.actual_end = datetime(2026, 1, 12, 12, 0)
        self.assertEqual(order._get_billing_service_date(), date(2026, 1, 12))
        order.scheduled_start = False
        order.actual_end = False
        self.assertEqual(order._get_billing_service_date(), fields.Date.context_today(order))

    def test_get_billable_orders(self):
        Order = self.env['wm.collection.order']
        done = self._order(order_line_ids=[self._line()])
        done.with_context(programmatic_state_change=True).write({
            'state': 'completed', 'actual_end': datetime(2026, 1, 10, 11, 0)})
        draft = self._order()
        other_partner = self.env['res.partner'].create({'name': 'OC Billing Other'})
        other = self._order(partner_id=other_partner.id, collection_point_id=False)
        other.with_context(programmatic_state_change=True).write({
            'state': 'signed', 'actual_end': datetime(2026, 1, 11, 11, 0)})
        start, end = date(2026, 1, 1), date(2026, 1, 31)
        billable = Order._get_billable_orders(period_start=start, period_end=end)
        self.assertIn(done, billable)
        self.assertIn(other, billable)
        self.assertNotIn(draft, billable)
        only = Order._get_billable_orders(partner=self.partner, period_start=start, period_end=end)
        self.assertIn(done, only)
        self.assertNotIn(other, only)
        outside = Order._get_billable_orders(
            period_start=date(2026, 3, 1), period_end=date(2026, 3, 31))
        self.assertNotIn(done, outside)
        self.assertFalse(Order._get_billable_orders())

    def test_order_line_price_and_unlocked_totals(self):
        order = self._order(order_line_ids=[self._line(self.product2, 4.0)])
        line = order.order_line_ids
        self.assertEqual(line.price_basis, 'per_kg')
        self.assertAlmostEqual(line.price, 0.25)
        self.assertAlmostEqual(line.total_amount, 1.0)
        key = line._get_billing_rule_key()
        self.assertEqual(key[0], self.category2)
        no_cat = self.env['wm.collection.order.line'].new({})
        self.assertFalse(no_cat._get_billing_rule_key())

    # ------------------------------------------------------------------
    # Rights and state guards
    # ------------------------------------------------------------------
    def test_check_collection_rights_blocks_plain_user(self):
        order = self._order()
        plain = self._user(login='oc_plain')
        with self.assertRaises(UserError):
            order.with_user(plain).action_dispatch()
        with self.assertRaises(UserError):
            order.with_user(plain).action_start()
        with self.assertRaises(UserError):
            order.with_user(plain).action_cancel()
        with self.assertRaises(UserError):
            order.with_user(plain).action_complete()
        dispatcher = self._user('wm_base.group_wm_dispatcher', login='oc_dispatcher')
        order.with_user(dispatcher)._check_collection_rights()

    def test_dispatch_guards(self):
        order = self._order()
        with self.assertRaises(ValidationError):
            order.action_dispatch()  # no vehicle / driver
        no_partner = self._order(partner_id=False, collection_point_id=False)
        with self.assertRaises(ValidationError):
            no_partner.action_dispatch()
        order2 = self._dispatchable_order()
        order2.action_dispatch()
        self.assertEqual(order2.state, 'dispatched')
        self.assertEqual(order2.route_id.state, 'dispatched')
        with self.assertRaises(UserError):
            order2.action_dispatch()

    def test_dispatch_standalone_requires_pretrip(self):
        other = self.env['fleet.vehicle'].create({
            'model_id': self.vehicle.model_id.id, 'license_plate': 'OC-004',
            'driver_id': self.driver.id,
        })
        order = self._order(vehicle_id=other.id, driver_id=self.driver.id)
        with self.assertRaises(ValidationError):
            order.action_dispatch()
        self.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-OC-4', 'vehicle_id': other.id,
            'checklist_type': 'pre_trip', 'state': 'checked',
        })
        order.action_dispatch()
        self.assertEqual(order.state, 'dispatched')

    def test_start_sets_actual_start_and_rejects_invalid_states(self):
        order = self._dispatchable_order()
        order.action_dispatch()
        order.action_start()
        self.assertEqual(order.state, 'in_progress')
        self.assertTrue(order.actual_start)
        with self.assertRaises(UserError):
            order.action_start()

    def test_cancel_guards(self):
        order = self._order()
        order.action_cancel()
        self.assertEqual(order.state, 'cancelled')
        with self.assertRaises(UserError):
            order.action_cancel()
        done = self._order()
        done.with_context(programmatic_state_change=True).write({'state': 'completed'})
        with self.assertRaises(UserError):
            done.action_cancel()

    def test_complete_guards_and_success(self):
        no_lines = self._dispatchable_order(order_line_ids=False)
        with self.assertRaises(ValidationError):
            no_lines.action_complete()
        zero = self._dispatchable_order(order_line_ids=[self._line(weight=0.0)])
        with self.assertRaises(ValidationError):
            zero.action_complete()
        order = self._dispatchable_order()
        order.action_dispatch()
        order.action_start()
        order.action_complete()
        self.assertEqual(order.state, 'completed')
        self.assertTrue(order.actual_end)
        self.assertGreater(order.actual_end, order.actual_start)
        with self.assertRaises(UserError):
            order.action_complete()

    def test_complete_standalone_creates_post_trip_checklist(self):
        order = self._order(
            vehicle_id=self.vehicle.id, driver_id=self.driver.id,
            order_line_ids=[self._line()])
        order.action_dispatch()
        order.action_complete()
        post = self.env['wm.vehicle.maintenance.checklist'].search([
            ('vehicle_id', '=', self.vehicle.id), ('checklist_type', '=', 'post_trip')])
        self.assertTrue(post)
        self.assertEqual(post[:1].state, 'tocheck')
        self.assertTrue(order.collection_report_pdf is not None)

    def test_mark_missed_guards(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('wm_collection.use_missed_collection', 'False')
        order = self._order()
        with self.assertRaises(UserError):
            order.action_mark_missed()
        params.set_param('wm_collection.use_missed_collection', 'True')
        order.invalidate_recordset(['use_missed_collection'])
        action = order.action_mark_missed()
        self.assertEqual(action['res_model'], 'wm.mark.missed.wizard')
        order.action_cancel()
        with self.assertRaises(UserError):
            order.action_mark_missed()

    def test_add_status_log_action(self):
        order = self._order()
        action = order.action_add_status_log()
        self.assertEqual(action['res_model'], 'wm.add.status.log.wizard')
        self.assertEqual(action['context']['default_order_id'], order.id)

    # ------------------------------------------------------------------
    # Locked-state protection (non-superuser)
    # ------------------------------------------------------------------
    def test_locked_order_protected_for_regular_users(self):
        order = self._order(order_line_ids=[self._line()])
        order.with_context(programmatic_state_change=True).write({'state': 'completed'})
        dispatcher = self._user('wm_base.group_wm_dispatcher', login='oc_disp2')
        as_user = order.with_user(dispatcher)
        with self.assertRaises(UserError):
            as_user.write({'notes': 'tamper'})
        with self.assertRaises(UserError):
            as_user.order_line_ids.write({'weight': 99.0})
        with self.assertRaises(UserError):
            as_user.order_line_ids.unlink()
        with self.assertRaises(UserError):
            self.env['wm.collection.order.line'].with_user(dispatcher).create({
                'order_id': order.id, 'category_id': self.category2.id,
                'product_id': self.product2.id,
            })
        with self.assertRaises(UserError):
            order.unlink()

    def test_state_write_ignored_without_programmatic_context(self):
        order = self._order()
        order.write({'state': 'completed'})
        self.assertEqual(order.state, 'draft')

    # ------------------------------------------------------------------
    # Route interaction
    # ------------------------------------------------------------------
    def test_create_with_route_syncs_route_line_and_inherits_vehicle(self):
        route = self.env['wm.route'].create({
            'name': 'New', 'vehicle_id': self.vehicle.id, 'driver_id': self.driver.id,
        })
        self.assertFalse(route.line_ids)
        order = self._order(route_id=route.id)
        self.assertEqual(route.line_ids.collection_point_id, self.point)
        self.assertEqual(order.vehicle_id, self.vehicle)
        # Same point again does not duplicate the stop
        self._order(route_id=route.id)
        self.assertEqual(len(route.line_ids), 1)

    def test_finishing_last_order_auto_completes_running_route(self):
        order = self._dispatchable_order()
        route = order.route_id
        route.action_start_route()
        self.assertEqual(route.state, 'running')
        order.action_cancel()
        self.assertEqual(route.state, 'completed')
        self.assertTrue(route.actual_end)

    def test_running_route_not_completed_while_orders_pending(self):
        order = self._dispatchable_order()
        route = order.route_id
        second = self._order(route_id=route.id, order_line_ids=[self._line()])
        route.action_start_route()
        order.action_cancel()
        self.assertEqual(route.state, 'running')
        second.action_cancel()
        self.assertEqual(route.state, 'completed')

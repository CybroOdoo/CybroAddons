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
import json
from datetime import date, datetime, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.wm_collection.models.wm_route import WmRoute


@tagged('post_install', '-at_install', 'wm_collection', 'route_coverage')
class TestRouteCoverage(TransactionCase):
    """Coverage for route computes, guards, map data, onchanges and crons."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'RC Partner'})
        Point = cls.env['wm.collection.point']
        cls.point1 = Point.create({'name': 'RC P1', 'partner_id': cls.partner.id,
                                   'latitude': 10.0, 'longitude': 10.0})
        cls.point2 = Point.create({'name': 'RC P2', 'partner_id': cls.partner.id,
                                   'latitude': 10.5, 'longitude': 10.5})
        cls.point3 = Point.create({'name': 'RC P3', 'partner_id': cls.partner.id,
                                   'latitude': 11.0, 'longitude': 11.0})
        cls.point_nogeo = Point.create({'name': 'RC P4', 'partner_id': cls.partner.id})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'RC Brand'})
        cls.fmodel = cls.env['fleet.vehicle.model'].create({'name': 'RC Truck', 'brand_id': brand.id})
        cls.driver = cls.env['res.partner'].create({'name': 'RC Driver'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.fmodel.id, 'license_plate': 'RC-001', 'driver_id': cls.driver.id,
            'wm_capacity_weight': 1000.0,
        })
        cls.Checklist = cls.env['wm.vehicle.maintenance.checklist']
        cls.checklist = cls.Checklist.create({
            'name': 'PRE-RC-1', 'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip', 'state': 'checked',
        })
        cls.category = cls.env['wm.waste.category'].create({'name': 'RC Cat', 'code': 'RCC', 'price': 1.0})

    def _route(self, points=None, **kw):
        points = self.point1 if points is None else points
        vals = {
            'name': 'New', 'vehicle_id': self.vehicle.id, 'driver_id': self.driver.id,
            'date': date(2026, 3, 2),
            'line_ids': [(0, 0, {'collection_point_id': p.id, 'sequence': 10 * (i + 1)})
                         for i, p in enumerate(points)],
        }
        vals.update(kw)
        return self.env['wm.route'].create(vals)

    def _order(self, route, point=None, **kw):
        vals = {
            'partner_id': self.partner.id,
            'collection_point_id': (point or self.point1).id,
            'route_id': route.id,
            'scheduled_start': datetime(2026, 3, 2, 8, 0),
            'scheduled_end': datetime(2026, 3, 2, 9, 0),
        }
        vals.update(kw)
        return self.env['wm.collection.order'].create(vals)

    def _user(self, login, group_xmlid=None):
        user = self.env['res.users'].create({
            'name': login, 'login': login, 'email': f'{login}@example.com'})
        if group_xmlid:
            self.env.ref(group_xmlid).write({'user_ids': [(4, user.id)]})
        return user

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    def test_is_inspected_from_pretrip_checklist(self):
        route = self._route()
        self.assertTrue(route.is_inspected)
        bare = self.env['fleet.vehicle'].create({'model_id': self.fmodel.id, 'license_plate': 'RC-002'})
        route2 = self._route(vehicle_id=bare.id, driver_id=False)
        self.assertFalse(route2.is_inspected)
        no_vehicle = self._route(vehicle_id=False, driver_id=False)
        self.assertFalse(no_vehicle._has_valid_pretrip_checklist())

    def test_pretrip_checklist_expires_after_vehicle_runs_a_route(self):
        vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.fmodel.id, 'license_plate': 'RC-003', 'driver_id': self.driver.id})
        self.Checklist.create({
            'name': 'PRE-RC-3', 'vehicle_id': vehicle.id,
            'checklist_type': 'pre_trip', 'state': 'checked', 'date': date(2026, 3, 1)})
        first = self._route(vehicle_id=vehicle.id, date=date(2026, 3, 2))
        second = self._route(vehicle_id=vehicle.id, date=date(2026, 3, 3))
        self.assertTrue(first._has_valid_pretrip_checklist())
        self.assertFalse(first._get_previous_started_route())
        first.action_start_route()
        first.invalidate_recordset()
        second.invalidate_recordset()
        self.assertEqual(second._get_previous_started_route(), first)
        self.assertFalse(second._has_valid_pretrip_checklist())
        self.assertFalse(second.is_inspected)
        # A fresh checklist done after the route started re-validates it
        self.Checklist.create({
            'name': 'PRE-RC-3B', 'vehicle_id': vehicle.id,
            'checklist_type': 'pre_trip', 'state': 'checked',
            'date': fields.Date.context_today(self) + timedelta(days=1)})
        self.assertTrue(second._has_valid_pretrip_checklist())

    def test_own_passed_inspection_false_without_inspections(self):
        self.assertFalse(self._route()._has_own_passed_inspection())

    def test_fill_level_percentage(self):
        route = self._route()
        order = self._order(route, order_line_ids=[(0, 0, {
            'category_id': self.category.id, 'weight': 250.0})])
        self.assertAlmostEqual(order.confirmed_weight, 250.0)
        self.assertAlmostEqual(route.fill_level_percentage, 25.0)
        self.vehicle.wm_capacity_weight = 0.0
        route.invalidate_recordset(['fill_level_percentage'])
        route._compute_fill_level_percentage()
        self.assertEqual(route.fill_level_percentage, 0.0)
        self.vehicle.wm_capacity_weight = 1000.0

    def test_is_ready_to_dispatch(self):
        route = self._route()
        route._compute_is_ready_to_dispatch()
        self.assertFalse(route.is_ready_to_dispatch)  # no orders
        self._order(route)
        route._compute_is_ready_to_dispatch()
        self.assertTrue(route.is_ready_to_dispatch)
        route.driver_id = False
        route._compute_is_ready_to_dispatch()
        self.assertFalse(route.is_ready_to_dispatch)
        route.driver_id = self.driver
        route.action_dispatch_route()
        route._compute_is_ready_to_dispatch()
        self.assertFalse(route.is_ready_to_dispatch)  # only to_start routes

    def test_counts_and_view_actions(self):
        route = self._route()
        self.assertEqual(route.collection_order_count, 0)
        self.assertEqual(route.inspection_count, 0)
        self.assertEqual(route.driver_history_count, 0)
        self.assertEqual(route.gate_entry_count, 0)
        order = self._order(route)
        self.assertEqual(route.collection_order_count, 1)
        action = route.action_view_collection_orders()
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['res_id'], order.id)
        self._order(route, self.point2)
        action = route.action_view_collection_orders()
        self.assertEqual(action['view_mode'], 'list,form')
        self.assertEqual(route.action_view_inspections()['res_model'], 'survey.user_input')
        self.assertEqual(route.action_view_driver_history()['res_model'], 'wm.driver.change.history')
        self.assertEqual(route.action_view_gate_entries()['res_model'], 'wm.facility.gate.entry')
        self.assertEqual(route.action_change_driver_wizard()['context']['default_route_id'], route.id)

    def test_view_driver_shift(self):
        route = self._route()
        self.assertFalse(route.action_view_driver_shift())
        route.action_start_route()
        action = route.action_view_driver_shift()
        self.assertEqual(action['res_id'], route.shift_id.id)

    def test_selected_point_ids(self):
        route = self._route(points=self.point1 | self.point2)
        self.assertEqual(route.selected_point_ids, self.point1 | self.point2)

    def test_use_settings(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('wm_collection.use_route_zones', 'True')
        route = self._route()
        route.invalidate_recordset(['use_route_zones'])
        self.assertTrue(route.use_route_zones)
        params.set_param('wm_collection.use_route_zones', 'False')
        route.invalidate_recordset(['use_route_zones'])
        self.assertFalse(route.use_route_zones)

    def test_valid_vehicle_ids_computes(self):
        route = self._route()
        # No done pre-trip surveys exist: empty recordset, no error
        self.assertFalse(route.valid_vehicle_ids)

    # ------------------------------------------------------------------
    # Map data / config
    # ------------------------------------------------------------------
    def test_route_map_data(self):
        route = self._route(points=self.point1 | self.point2 | self.point_nogeo)
        data = json.loads(route.route_map_data)
        names = [p['name'] for p in data['route_points']]
        self.assertEqual(sorted(names), ['RC P1', 'RC P2'])
        self.assertTrue(all(p['is_route_point'] for p in data['route_points']))
        self.assertEqual([p['index'] for p in data['route_points']], [1, 2])
        other_names = [p['name'] for p in data['other_points']]
        self.assertIn('RC P3', other_names)
        self.assertNotIn('RC P1', other_names)
        self.assertNotIn('RC P4', other_names)  # no coordinates
        route.with_context(programmatic_state_change=True).write({'state': 'completed'})
        route.invalidate_recordset(['route_map_data'])
        route._compute_route_map_data()
        self.assertEqual(json.loads(route.route_map_data)['other_points'], [])

    def test_get_map_config(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('wm_collection.map_tile_url', ' https://tiles.example.com/{z}/{x}/{y}.png ')
        params.set_param('wm_collection.osrm_router_url', 'javascript:alert(1)')
        config = self.env['wm.route'].get_map_config()
        self.assertEqual(config['tile_url'], 'https://tiles.example.com/{z}/{x}/{y}.png')
        self.assertFalse(config['osrm_url'])
        params.set_param('wm_collection.map_tile_url', '')
        self.assertFalse(self.env['wm.route'].get_map_config()['tile_url'])

    def test_action_view_route_map_optimizes_to_start(self):
        route = self._route(points=self.point1 | self.point3 | self.point2)
        action = route.action_view_route_map()
        self.assertEqual(action['tag'], 'wm_collection.route_map_client_action')
        self.assertEqual(action['params']['route_id'], route.id)
        seqs = route.line_ids.sorted('sequence').mapped('sequence')
        self.assertEqual(seqs, [10, 20, 30])

    # ------------------------------------------------------------------
    # Onchanges
    # ------------------------------------------------------------------
    def test_onchange_zone_assigns_defaults(self):
        zone = self.env['wm.service.zone'].create({
            'name': 'RC Zone', 'default_vehicle_id': self.vehicle.id})
        route = self.env['wm.route'].new({'zone_id': zone.id})
        route._onchange_zone_id()
        self.assertEqual(route.vehicle_id, self.vehicle)
        self.assertEqual(route.driver_id, self.driver)
        zone2 = self.env['wm.service.zone'].create({
            'name': 'RC Zone 2', 'default_driver_id': self.driver.id})
        route2 = self.env['wm.route'].new({'zone_id': zone2.id})
        route2._onchange_zone_id()
        self.assertEqual(route2.driver_id, self.driver)
        self.assertFalse(route2.vehicle_id)

    def test_onchange_vehicle_sets_driver(self):
        route = self.env['wm.route'].new({'vehicle_id': self.vehicle.id})
        route._onchange_vehicle_id()
        self.assertEqual(route.driver_id, self.driver)
        route.vehicle_id = False
        route._onchange_vehicle_id()
        self.assertFalse(route.driver_id)

    def test_onchange_double_booking_warning(self):
        existing = self._route()
        probe = self.env['wm.route'].new({
            'date': existing.date, 'vehicle_id': self.vehicle.id, 'driver_id': self.driver.id})
        res = probe._onchange_check_double_booking()
        message = res['warning']['message']
        self.assertIn('RC-001', message)
        self.assertIn('RC Driver', message)
        free = self.env['wm.route'].new({
            'date': date(2030, 1, 1), 'vehicle_id': self.vehicle.id})
        self.assertFalse(free._onchange_check_double_booking())
        self.assertFalse(self.env['wm.route'].new({})._onchange_check_double_booking())

    # ------------------------------------------------------------------
    # Rights and lifecycle guards
    # ------------------------------------------------------------------
    def test_route_rights_block_plain_user(self):
        route = self._route()
        plain = self._user('rc_plain')
        for method in ('action_dispatch_route', 'action_start_route',
                       'action_complete_route', 'action_cancel_route'):
            with self.assertRaises(UserError, msg=method):
                getattr(route.with_user(plain), method)()
        dispatcher = self._user('rc_disp', 'wm_base.group_wm_dispatcher')
        route.with_user(dispatcher)._check_route_rights()

    def test_start_route_guards(self):
        route = self._route(vehicle_id=False, driver_id=False)
        with self.assertRaises(ValidationError):
            route.action_start_route()
        route2 = self._route()
        route2.action_start_route()
        with self.assertRaises(UserError):
            route2.action_start_route()

    def test_start_route_reuses_active_shift(self):
        shift = self.env['wm.driver.shift'].create({
            'driver_id': self.driver.id, 'vehicle_id': self.vehicle.id,
            'shift_start': fields.Datetime.now()})
        route = self._route()
        route.action_start_route()
        self.assertEqual(route.shift_id, shift)

    def test_complete_route_closes_shift_and_rejects_repeat(self):
        route = self._route()
        route.action_start_route()
        shift = route.shift_id
        route.action_complete_route()
        self.assertEqual(route.state, 'completed')
        self.assertTrue(shift.shift_end)
        with self.assertRaises(UserError):
            route.action_complete_route()
        with self.assertRaises(UserError):
            route.action_cancel_route()

    def test_cancel_route_resets_orders_and_closes_shift(self):
        route = self._route()
        order = self._order(route)
        route.action_dispatch_route()
        self.assertEqual(order.state, 'dispatched')
        route.action_start_route()
        shift = route.shift_id
        route.action_cancel_route()
        self.assertEqual(route.state, 'to_start')
        self.assertFalse(route.actual_start)
        self.assertFalse(route.shift_id)
        self.assertEqual(order.state, 'draft')
        self.assertTrue(shift.shift_end)

    def test_dispatch_route_guards(self):
        no_vehicle = self._route(vehicle_id=False, driver_id=False)
        with self.assertRaises(ValidationError):
            no_vehicle.action_dispatch_route()
        no_lines = self._route(points=self.env['wm.collection.point'])
        with self.assertRaises(ValidationError):
            no_lines.action_dispatch_route()
        bare = self.env['fleet.vehicle'].create({'model_id': self.fmodel.id, 'license_plate': 'RC-009'})
        uninspected = self._route(vehicle_id=bare.id, driver_id=False)
        with self.assertRaises(ValidationError):
            uninspected.action_dispatch_route()
        ok = self._route()
        ok.action_dispatch_route()
        with self.assertRaises(UserError):
            ok.action_dispatch_route()

    def test_dispatch_moves_unrouted_orders_at_route_points(self):
        route = self._route()
        unrouted = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id, 'collection_point_id': self.point1.id,
            'scheduled_start': datetime(2026, 3, 2, 10, 0),
            'scheduled_end': datetime(2026, 3, 2, 11, 0),
        })
        other_day = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id, 'collection_point_id': self.point1.id,
            'scheduled_start': datetime(2026, 3, 5, 10, 0),
            'scheduled_end': datetime(2026, 3, 5, 11, 0),
        })
        route.action_dispatch_route()
        self.assertEqual(unrouted.state, 'dispatched')
        self.assertEqual(unrouted.route_id, route)
        self.assertEqual(other_day.state, 'draft')
        self.assertFalse(other_day.route_id)

    def test_optimize_locked_after_dispatch(self):
        route = self._route(points=self.point1 | self.point2)
        route.action_dispatch_route()
        with self.assertRaises(UserError):
            route.action_optimize_route()
        route.with_context(bypass_sequence_lock=True).action_optimize_route()

    def test_remove_collection_point_removes_draft_orders(self):
        route = self._route(points=self.point1 | self.point2)
        order = self._order(route, self.point2)
        self.assertTrue(route.action_remove_collection_point(self.point2.id))
        self.assertEqual(route.line_ids.collection_point_id, self.point1)
        self.assertFalse(order.exists())
        # Unknown point is a no-op
        self.assertTrue(route.action_remove_collection_point(self.point3.id))
        self.assertEqual(len(route.line_ids), 1)

    def test_write_vehicle_lock_and_completed_lock(self):
        other = self.env['fleet.vehicle'].create({'model_id': self.fmodel.id, 'license_plate': 'RC-010'})
        route = self._route()
        route.action_dispatch_route()
        with self.assertRaises(UserError):
            route.write({'vehicle_id': other.id})
        route.write({'vehicle_id': self.vehicle.id})  # unchanged value is fine
        route.action_start_route()
        route.action_complete_route()
        dispatcher = self._user('rc_disp2', 'wm_base.group_wm_dispatcher')
        with self.assertRaises(UserError):
            route.with_user(dispatcher).write({'zone_id': False, 'date': date(2026, 4, 1)})
        with self.assertRaises(UserError):
            route.with_user(dispatcher).line_ids.write({'sequence': 99})
        with self.assertRaises(UserError):
            route.with_user(dispatcher).line_ids.unlink()
        with self.assertRaises(UserError):
            self.env['wm.route.line'].with_user(dispatcher).create({
                'route_id': route.id, 'collection_point_id': self.point2.id})

    def test_unlink_guard(self):
        route = self._route()
        route.action_start_route()
        with self.assertRaises(UserError):
            route.unlink()
        route.with_context(programmatic_state_change=True).write({'state': 'to_start'})
        route.unlink()
        self.assertFalse(route.exists())

    def test_action_inspect_vehicle_without_survey(self):
        route = self._route()
        survey = self.env['survey.survey'].search([('title', 'ilike', 'Pre-Trip')], limit=1)
        res = route.action_inspect_vehicle()
        if survey:
            self.assertEqual(res['res_model'], 'survey.user_input')
        else:
            self.assertIsNone(res)

    # ------------------------------------------------------------------
    # Crons
    # ------------------------------------------------------------------
    def _ready_route(self, point):
        route = self._route(points=point)
        self._order(route, point)
        return route

    def test_cron_auto_dispatch_disabled_does_not_dispatch(self):
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.auto_dispatch_enabled', 'False')
        route = self._ready_route(self.point1)
        self.env['wm.route']._cron_auto_dispatch_ready_routes()
        self.assertTrue(route.is_ready_to_dispatch)
        self.assertEqual(route.state, 'to_start')

    def test_cron_auto_dispatch_isolates_failing_route(self):
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.auto_dispatch_enabled', 'True')
        route_bad = self._ready_route(self.point1)
        route_good = self._ready_route(self.point2)
        real = WmRoute.action_dispatch_route

        def _flaky(rec):
            if rec == route_bad:
                raise UserError("boom")
            return real(rec)

        with patch.object(WmRoute, 'action_dispatch_route', autospec=True, side_effect=_flaky):
            self.env['wm.route']._cron_auto_dispatch_ready_routes()
        self.assertEqual(route_bad.state, 'to_start')
        self.assertEqual(route_good.state, 'dispatched')
        self.assertEqual(route_good.collection_order_ids.state, 'dispatched')

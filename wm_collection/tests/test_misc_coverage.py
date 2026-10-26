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

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_collection', 'misc_coverage')
class TestMiscCoverage(TransactionCase):
    """Coverage for schedules, shifts, zones, missed-collection cron, status logs, wizards and points."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'MC Partner'})
        cls.driver = cls.env['res.partner'].create({'name': 'MC Driver'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'MC Point', 'partner_id': cls.partner.id,
            'latitude': 12.5, 'longitude': 45.25,
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'MC Brand'})
        cls.fmodel = cls.env['fleet.vehicle.model'].create({'name': 'MC Truck', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.fmodel.id, 'license_plate': 'MC-001', 'driver_id': cls.driver.id})
        cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-MC-1', 'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip', 'state': 'checked'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'MC Cat', 'code': 'MCC', 'price': 1.0})

    def _route(self, **kw):
        vals = {
            'name': 'New', 'vehicle_id': self.vehicle.id, 'driver_id': self.driver.id,
            'date': date(2026, 5, 4),
            'line_ids': [(0, 0, {'collection_point_id': self.point.id})],
        }
        vals.update(kw)
        return self.env['wm.route'].create(vals)

    def _order(self, **kw):
        vals = {
            'partner_id': self.partner.id, 'collection_point_id': self.point.id,
            'scheduled_start': datetime(2026, 5, 4, 8, 0),
            'scheduled_end': datetime(2026, 5, 4, 9, 0),
        }
        vals.update(kw)
        return self.env['wm.collection.order'].create(vals)

    # ------------------------------------------------------------------
    # Schedule
    # ------------------------------------------------------------------
    def test_schedule_next_occurrence(self):
        route = self._route()
        base = datetime(2026, 1, 31, 6, 0)
        expected = {
            'daily': datetime(2026, 2, 1, 6, 0),
            'weekly': datetime(2026, 2, 7, 6, 0),
            'biweekly': datetime(2026, 2, 14, 6, 0),
            'monthly': datetime(2026, 2, 28, 6, 0),
        }
        for recurrence, result in expected.items():
            schedule = self.env['wm.schedule'].create({
                'name': recurrence, 'route_id': route.id, 'recurrence': recurrence})
            self.assertEqual(schedule._get_next_occurrence(base), result, recurrence)

    def test_schedule_occurrence_route_reuses_or_copies_template(self):
        template = self._route(date=date(2026, 5, 4))
        schedule = self.env['wm.schedule'].create({
            'name': 'S', 'route_id': template.id, 'recurrence': 'daily'})
        same_day = schedule._get_occurrence_route(datetime(2026, 5, 4, 12, 0))
        self.assertEqual(same_day, template)
        next_day = schedule._get_occurrence_route(datetime(2026, 5, 5, 12, 0))
        self.assertNotEqual(next_day, template)
        self.assertEqual(next_day.date, date(2026, 5, 5))
        self.assertEqual(next_day.line_ids.collection_point_id, self.point)
        self.assertEqual(next_day.vehicle_id, self.vehicle)
        template.action_start_route()
        again = schedule._get_occurrence_route(datetime(2026, 5, 4, 12, 0))
        self.assertNotEqual(again, template)

    def test_schedule_process_catches_up_once(self):
        template = self._route(date=fields.Date.context_today(self) - timedelta(days=10))
        schedule = self.env['wm.schedule'].create({
            'name': 'Catch up', 'route_id': template.id, 'recurrence': 'daily',
            'next_run_date': fields.Datetime.now() - timedelta(days=5)})
        self.env['wm.schedule']._process_schedules()
        self.assertGreater(schedule.next_run_date, fields.Datetime.now())
        orders = self.env['wm.collection.order'].search([
            ('collection_point_id', '=', self.point.id), ('route_id', '!=', False)])
        self.assertEqual(len(orders), 1)

    # ------------------------------------------------------------------
    # Driver shift
    # ------------------------------------------------------------------
    def test_driver_shift_computes(self):
        start = datetime(2026, 5, 4, 8, 0)
        shift = self.env['wm.driver.shift'].create({
            'driver_id': self.driver.id, 'vehicle_id': self.vehicle.id,
            'shift_start': start, 'shift_end': start + timedelta(hours=7, minutes=30)})
        self.assertAlmostEqual(shift.hours_driven, 7.5)
        self.assertIn('MC Driver', shift.name)
        self.assertEqual(shift.route_count, 0)
        route = self._route(shift_id=shift.id)
        shift.invalidate_recordset(['route_count'])
        self.assertEqual(shift.route_count, 1)
        action = shift.action_view_routes()
        self.assertEqual(action['domain'], [('shift_id', '=', shift.id)])
        self.assertTrue(route)

    def test_driver_shift_open_hours_use_now(self):
        shift = self.env['wm.driver.shift'].create({
            'driver_id': self.driver.id, 'vehicle_id': self.vehicle.id,
            'shift_start': fields.Datetime.now() - timedelta(hours=2)})
        self.assertAlmostEqual(shift.hours_driven, 2.0, delta=0.05)
        empty = self.env['wm.driver.shift'].new({})
        self.assertEqual(empty.hours_driven, 0.0)
        self.assertEqual(empty.name, 'New')

    def test_driver_shift_onchange_vehicle(self):
        shift = self.env['wm.driver.shift'].new({'vehicle_id': self.vehicle.id})
        shift._onchange_vehicle_id()
        self.assertEqual(shift.driver_id, self.driver)
        shift.vehicle_id = False
        shift._onchange_vehicle_id()
        self.assertFalse(shift.driver_id)

    # ------------------------------------------------------------------
    # Zone / fleet
    # ------------------------------------------------------------------
    def test_service_zone_count_and_onchange(self):
        zone = self.env['wm.service.zone'].create({'name': 'MC Zone'})
        self.assertEqual(zone.collection_point_count, 0)
        self.point.zone_id = zone
        self.assertEqual(zone.collection_point_count, 1)
        zone.default_vehicle_id = self.vehicle
        zone._onchange_default_vehicle_id()
        self.assertEqual(zone.default_driver_id, self.driver)
        zone.default_vehicle_id = False
        zone._onchange_default_vehicle_id()
        self.assertFalse(zone.default_driver_id)

    def test_fleet_vehicle_is_running(self):
        self.assertFalse(self.vehicle.wm_is_running)
        route = self._route()
        route.action_start_route()
        self.vehicle.invalidate_recordset(['wm_is_running'])
        self.assertTrue(self.vehicle.wm_is_running)
        route.action_complete_route()
        self.vehicle.invalidate_recordset(['wm_is_running'])
        self.assertFalse(self.vehicle.wm_is_running)
        order = self._order(vehicle_id=self.vehicle.id, driver_id=self.driver.id)
        order.action_dispatch()
        self.vehicle.invalidate_recordset(['wm_is_running'])
        self.assertTrue(self.vehicle.wm_is_running)

    # ------------------------------------------------------------------
    # Missed collection cron
    # ------------------------------------------------------------------
    def _missed(self, days_ago=1):
        reason = self.env['wm.missed.reason'].search([], limit=1) or \
            self.env['wm.missed.reason'].create({'name': 'MC Reason'})
        order = self._order()
        return self.env['wm.missed.collection'].create({
            'order_id': order.id, 'reason_id': reason.id,
            'missed_date': fields.Datetime.now() - timedelta(days=days_ago)})

    def test_missed_collection_sequence_reference(self):
        missed = self._missed()
        self.assertNotEqual(missed.name, 'New')

    def test_weekly_review_cron(self):
        Missed = self.env['wm.missed.collection']
        Activity = self.env['mail.activity']
        params = self.env['ir.config_parameter'].sudo()
        model_id = self.env['ir.model']._get_id('wm.missed.collection')
        domain = [('res_model_id', '=', model_id), ('summary', '=', 'Weekly Missed Collection Review')]
        params.set_param('wm_collection.use_missed_collection', 'False')
        self._missed()
        Missed._cron_weekly_review_reminder()
        self.assertFalse(Activity.search(domain))
        params.set_param('wm_collection.use_missed_collection', 'True')
        Missed.search([]).write({'missed_date': fields.Datetime.now() - timedelta(days=30)})
        Missed._cron_weekly_review_reminder()
        self.assertFalse(Activity.search(domain))  # nothing in the last 7 days
        self._missed(days_ago=1)
        self._missed(days_ago=2)
        Missed._cron_weekly_review_reminder()
        activity = Activity.search(domain)
        self.assertEqual(len(activity), 1)
        self.assertIn('2 missed collection(s)', activity.note)
        self.assertIn('MC Partner (2)', activity.note)

    # ------------------------------------------------------------------
    # Status log / wizard
    # ------------------------------------------------------------------
    def test_log_stop_event_validation_and_defaults(self):
        Log = self.env['wm.collection.order.status.log']
        order = self._order()
        with self.assertRaises(ValidationError):
            Log.log_stop_event(order, '')
        with self.assertRaises(ValidationError):
            Log.log_stop_event(self.env['wm.collection.order'], 'arrived')
        log = Log.log_stop_event(order, 'arrived', note='at gate')
        # Coordinates fall back to the collection point
        self.assertAlmostEqual(log.latitude, 12.5)
        self.assertAlmostEqual(log.longitude, 45.25)
        self.assertEqual(log.driver_id, self.env.user)
        self.assertEqual(log.note, 'at gate')
        explicit = Log.log_stop_event(order, 'weighed', latitude=1.0, longitude=2.0)
        self.assertAlmostEqual(explicit.latitude, 1.0)
        self.assertEqual(order.status_log_ids, log | explicit)

    def test_client_uuid_unique(self):
        Log = self.env['wm.collection.order.status.log']
        order = self._order()
        Log.create({'order_id': order.id, 'status': 'arrived', 'client_uuid': 'uuid-1'})
        with self.assertRaises(Exception), self.cr.savepoint():
            Log.create({'order_id': order.id, 'status': 'lifted', 'client_uuid': 'uuid-1'})

    def test_started_and_completed_events_drive_order_state(self):
        route = self._route()
        order = self._order(route_id=route.id, order_line_ids=[(0, 0, {
            'category_id': self.category.id, 'weight': 5.0})])
        route.action_dispatch_route()
        Log = self.env['wm.collection.order.status.log']
        started = datetime(2026, 5, 4, 8, 30)
        Log.log_stop_event(order, 'started', timestamp=started)
        self.assertEqual(order.state, 'in_progress')
        self.assertEqual(order.actual_start, started)
        # Out-of-order completion timestamp is clamped after the start
        Log.log_stop_event(order, 'completed', timestamp=started - timedelta(minutes=10))
        self.assertEqual(order.state, 'completed')
        self.assertEqual(order.actual_end, started + timedelta(seconds=1))
        # Further events are just logged
        Log.log_stop_event(order, 'flagged')
        self.assertEqual(order.state, 'completed')

    def test_status_wizard_default_location_and_confirm(self):
        Wizard = self.env['wm.add.status.log.wizard']
        order = self._order()
        defaults = Wizard.with_context(default_order_id=order.id).default_get(
            ['order_id', 'latitude', 'longitude'])
        self.assertAlmostEqual(defaults['latitude'], 12.5)
        self.assertAlmostEqual(defaults['longitude'], 45.25)
        no_point = self._order(collection_point_id=False)
        self.assertEqual(Wizard._get_default_location(no_point), (0.0, 0.0))
        wizard = Wizard.create({'order_id': order.id, 'status': 'arrived', 'note': 'hi'})
        wizard.latitude = 0.0
        wizard.longitude = 0.0
        wizard._onchange_order_id()
        self.assertAlmostEqual(wizard.latitude, 12.5)
        res = wizard.action_confirm()
        self.assertEqual(res['type'], 'ir.actions.act_window_close')
        self.assertEqual(order.status_log_ids.status, 'arrived')
        self.assertEqual(order.status_log_ids.note, 'hi')

    # ------------------------------------------------------------------
    # Change driver wizard
    # ------------------------------------------------------------------
    def test_change_driver_success_updates_route_and_active_orders(self):
        route = self._route()
        active = self._order(route_id=route.id)
        done = self._order(route_id=route.id)
        done.with_context(programmatic_state_change=True).write({'state': 'completed'})
        new_driver = self.env['res.partner'].create({'name': 'MC New Driver'})
        self.env['wm.change.driver.wizard'].create({
            'route_id': route.id, 'new_driver_id': new_driver.id, 'reason': 'Sick leave',
        }).action_change_driver()
        self.assertEqual(route.driver_id, new_driver)
        self.assertEqual(active.driver_id, new_driver)
        self.assertEqual(done.driver_id, self.driver)
        history = self.env['wm.driver.change.history'].search([('route_id', '=', route.id)])
        self.assertEqual(history.old_driver_id, self.driver)
        self.assertEqual(history.new_driver_id, new_driver)
        self.assertEqual(history.reason, 'Sick leave')
        self.assertEqual(route.driver_history_count, 1)

    def test_change_driver_rejects_busy_or_booked_driver(self):
        route = self._route()
        Wizard = self.env['wm.change.driver.wizard']
        busy = self.env['res.partner'].create({'name': 'MC Busy'})
        self.env['wm.driver.shift'].create({
            'driver_id': busy.id, 'vehicle_id': self.vehicle.id,
            'shift_start': fields.Datetime.now()})
        with self.assertRaises(ValidationError):
            Wizard.create({'route_id': route.id, 'new_driver_id': busy.id,
                           'reason': 'x'}).action_change_driver()
        booked = self.env['res.partner'].create({'name': 'MC Booked'})
        self._route(driver_id=booked.id)
        with self.assertRaises(ValidationError):
            Wizard.create({'route_id': route.id, 'new_driver_id': booked.id,
                           'reason': 'x'}).action_change_driver()
        self.assertEqual(route.driver_id, self.driver)

    # ------------------------------------------------------------------
    # Report wizards
    # ------------------------------------------------------------------
    def test_report_wizards_date_range_and_print(self):
        for model in ('wm.collection.order.report.wizard', 'wm.missed.collection.report.wizard'):
            Wizard = self.env[model]
            with self.assertRaises(ValidationError, msg=model):
                Wizard.create({'date_from': date(2026, 5, 10), 'date_to': date(2026, 5, 1)})
            wizard = Wizard.create({'date_from': date(2026, 5, 1), 'date_to': date(2026, 5, 10)})
            action = wizard.action_print_pdf()
            self.assertIn(action['type'], ('ir.actions.report', 'ir.actions.act_window'), model)

    # ------------------------------------------------------------------
    # Collection point
    # ------------------------------------------------------------------
    def test_collection_point_computes_and_actions(self):
        point = self.env['wm.collection.point'].create({
            'name': 'MC Addr', 'street': '1 Main St', 'city': 'Springfield', 'zip': '12345',
            'country_id': self.env.ref('base.us').id,
            'latitude': 1.0, 'longitude': 1.0,
        })
        self.assertEqual(point.contact_address, '1 Main St, Springfield, 12345, United States')
        self.assertEqual(point.container_count, 0)
        action = point.action_view_containers()
        self.assertEqual(action['domain'], [('collection_point_id', '=', point.id)])
        callout = self.partner and point.action_log_emergency_callout()
        self.assertEqual(callout['context']['default_collection_point_id'], point.id)
        self.assertEqual(callout['context']['default_event_type'], 'emergency_callout')

    def test_collection_point_use_settings(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('wm_collection.use_route_zones', 'True')
        self.point.invalidate_recordset(['use_route_zones'])
        self.assertTrue(self.point.use_route_zones)
        params.set_param('wm_collection.use_route_zones', 'False')
        self.point.invalidate_recordset(['use_route_zones'])
        self.assertFalse(self.point.use_route_zones)

    def test_collection_point_onchange_partner_fills_blank_address(self):
        partner = self.env['res.partner'].create({
            'name': 'MC Addr Partner', 'street': '9 Elm', 'city': 'Gotham', 'zip': '99999',
            'country_id': self.env.ref('base.us').id,
            'partner_latitude': 3.5, 'partner_longitude': 4.5})
        point = self.env['wm.collection.point'].new({
            'name': 'P', 'partner_id': partner.id, 'city': 'Keep City'})
        point._onchange_partner_id()
        self.assertEqual(point.street, '9 Elm')
        self.assertEqual(point.city, 'Keep City')
        self.assertEqual(point.zip, '99999')
        self.assertAlmostEqual(point.latitude, 3.5)
        self.assertAlmostEqual(point.longitude, 4.5)

    # ------------------------------------------------------------------
    # Settings / map-view wizard
    # ------------------------------------------------------------------
    def test_settings_map_urls_round_trip(self):
        settings = self.env['res.config.settings'].create({
            'wm_map_tile_url': 'https://tiles.example.com/{z}/{x}/{y}.png',
            'wm_osrm_router_url': 'https://osrm.example.com/route/v1/driving',
        })
        settings.set_values()
        params = self.env['ir.config_parameter'].sudo()
        self.assertEqual(params.get_param('wm_collection.map_tile_url'),
                         'https://tiles.example.com/{z}/{x}/{y}.png')
        values = self.env['res.config.settings'].get_values()
        self.assertEqual(values['wm_osrm_router_url'], 'https://osrm.example.com/route/v1/driving')
        blank = self.env['res.config.settings'].create({
            'wm_map_tile_url': False, 'wm_osrm_router_url': False})
        blank.set_values()
        self.assertEqual(params.get_param('wm_collection.osrm_router_url'),
                         'https://router.project-osrm.org/route/v1/driving')

    def test_map_view_wizard_builds_arch_and_updates_actions(self):
        model = self.env['ir.model']._get('wm.collection.point')
        action = self.env['ir.actions.act_window'].create({
            'name': 'MC Action', 'res_model': 'wm.collection.point', 'view_mode': 'list,form'})
        Wizard = self.env['map.view.config.wizard']
        with self.assertRaises(UserError):
            Wizard.create({'model_id': model.id, 'lat_field': 'latitude'}).action_create_map_view()
        wizard = Wizard.create({
            'model_id': model.id, 'action_ids': [(6, 0, action.ids)],
            'lat_field': 'latitude', 'lng_field': 'longitude', 'address_field': 'contact_address',
            'view_position': 'after_list'})
        arch = wizard._build_map_view_arch()
        self.assertIn('<field name="latitude" string="Latitude"/>', arch)
        partner_field = self.env['ir.model.fields']._get('wm.collection.point', 'partner_id')
        wizard.partner_field_id = partner_field
        self.assertIn('res_partner="partner_id"', wizard._build_map_view_arch())
        wizard._update_action_view_mode(action)
        self.assertEqual(action.view_mode, 'list,wm_map,form')
        wizard.view_position = 'end'
        wizard._update_action_view_mode(action)
        self.assertEqual(action.view_mode, 'list,form,wm_map')
        self.assertTrue(wizard._get_partner_field_selection())

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
#############################################################################
from datetime import datetime, time, timedelta
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_collection')
class TestCollectionDecisions(TransactionCase):
    """Regression tests for the product decisions on routes, rentals,
    pre-trip inspection validity and gate-entry custody automation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.context_today(cls.env.user)
        cls.category = cls.env['wm.waste.category'].create({'name': 'Dec Paper', 'code': 'DECPAP'})
        cls.product = cls.env['product.product'].create({
            'name': 'Dec Paper Waste',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Dec Generator'})
        cls.driver = cls.env['res.partner'].create({'name': 'Dec Driver'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Dec Bay', 'partner_id': cls.partner.id})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Dec Trucks'})
        cls.vmodel = cls.env['fleet.vehicle.model'].create({'name': 'Dec Hauler', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': cls.vmodel.id, 'license_plate': 'DEC-001'})
        cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-TRIP-DEC',
            'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip',
            'state': 'checked',
            'date': cls.today,
        })
        cls.route = cls.env['wm.route'].create({
            'date': cls.today,
            'vehicle_id': cls.vehicle.id,
            'driver_id': cls.driver.id,
            'line_ids': [(0, 0, {'collection_point_id': cls.point.id, 'sequence': 10})],
        })

    def _order(self, start, **vals):
        return self.env['wm.collection.order'].create(dict({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'scheduled_start': start,
            'scheduled_end': start + timedelta(hours=1),
            'order_line_ids': [(0, 0, {
                'category_id': self.category.id,
                'product_id': self.product.id,
                'weight': 50.0,
            })],
        }, **vals))

    def _user(self, login, group_xmlid):
        return self.env['res.users'].create({
            'name': login,
            'login': login,
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref(group_xmlid).id])],
        })

    def _vehicle(self, plate):
        return self.env['fleet.vehicle'].create({'model_id': self.vmodel.id, 'license_plate': plate})

    def _checklist(self, vehicle, date, state='checked'):
        return self.env['wm.vehicle.maintenance.checklist'].create({
            'name': f'PRE-TRIP-{vehicle.license_plate}-{date}',
            'vehicle_id': vehicle.id,
            'checklist_type': 'pre_trip',
            'state': state,
            'date': date,
        })

    def _just_started(self):
        # Datetime.now() drops microseconds; one extra second keeps the start
        # strictly after every record created earlier in this transaction.
        return fields.Datetime.now() + timedelta(seconds=1)

    def _mark_started(self, route, start, state='running'):
        route.with_context(programmatic_state_change=True).write({'state': state, 'actual_start': start})

    # Decision 1: route state buttons hidden from pure drivers -------------
    def test_route_state_buttons_hidden_from_pure_driver(self):
        """Pure drivers do not get Dispatch/Start/Complete/Cancel; dispatchers do."""
        state_buttons = {'action_dispatch_route', 'action_start_route',
                         'action_complete_route', 'action_cancel_route'}
        view_id = self.env.ref('wm_collection.view_wm_route_form').id

        def header_buttons(user):
            arch = self.env['wm.route'].with_user(user).get_view(view_id, 'form')['arch']
            return set(etree.fromstring(arch).xpath('//header/button/@name'))

        driver = self._user('dec_pure_driver', 'wm_base.group_wm_driver')
        dispatcher = self._user('dec_dispatcher', 'wm_base.group_wm_dispatcher')
        self.assertFalse(header_buttons(driver) & state_buttons)
        self.assertEqual(header_buttons(dispatcher) & state_buttons, state_buttons)

    # Decision 3: rental invoices bill every full elapsed period -----------
    def _container(self, period, deployed_date):
        ctype = self.env['wm.container.type'].create({
            'name': f'Dec Bin {period}', 'code': f'DEC{period[:3].upper()}', 'capacity_volume': 240.0,
        })
        container = self.env['wm.container'].create({
            'name': f'BIN-DEC-{period}',
            'container_type_id': ctype.id,
            'collection_point_id': self.point.id,
            'rental_rate': 10.0,
            'rental_period': period,
        })
        container.deployed_date = deployed_date
        return container

    def _invoice_qty(self, container):
        action = container.action_create_rental_invoice()
        return self.env['account.move'].browse(action['res_id']).invoice_line_ids.quantity

    def test_rental_weekly_bills_full_weeks_and_carries_partial(self):
        today = fields.Date.today()
        deployed = today - timedelta(days=17)
        container = self._container('weekly', deployed)
        self.assertEqual(self._invoice_qty(container), 2.0)
        # Advanced by exactly two weeks, the 3 extra days carry over.
        self.assertEqual(container.last_invoiced_date, deployed + timedelta(weeks=2))
        with self.assertRaises(UserError):
            container.action_create_rental_invoice()
        # Four more days elapse: the carried 3 days complete a new week.
        container.last_invoiced_date = today - timedelta(days=7)
        self.assertEqual(self._invoice_qty(container), 1.0)
        self.assertEqual(container.last_invoiced_date, today)

    def test_rental_monthly_bills_whole_months(self):
        today = fields.Date.today()
        deployed = today - relativedelta(months=3, days=5)
        container = self._container('monthly', deployed)
        self.assertEqual(self._invoice_qty(container), 3.0)
        self.assertEqual(container.last_invoiced_date, deployed + relativedelta(months=3))
        with self.assertRaises(UserError):
            container.action_create_rental_invoice()

    def test_rental_refused_before_first_full_period(self):
        container = self._container('monthly', fields.Date.today() - timedelta(days=10))
        with self.assertRaises(UserError):
            container.action_create_rental_invoice()
        self.assertFalse(container.invoice_ids)
        self.assertFalse(container.last_invoiced_date)

    def test_rental_daily_bills_every_day(self):
        today = fields.Date.today()
        container = self._container('daily', today - timedelta(days=6))
        self.assertEqual(self._invoice_qty(container), 6.0)
        self.assertEqual(container.last_invoiced_date, today)

    def test_rental_flat_fee_once_per_deployment(self):
        container = self._container('flat', fields.Date.today() - timedelta(days=40))
        self.assertEqual(self._invoice_qty(container), 1.0)
        with self.assertRaises(UserError):
            container.action_create_rental_invoice()

    # Decision 6: cancel closes (never deletes) the shift --------------------
    def test_cancel_route_closes_shift_with_note(self):
        self._order(datetime.combine(self.today, time(10, 0)), route_id=self.route.id)
        self.route.action_dispatch_route()
        self.route.action_start_route()
        shift = self.route.shift_id
        self.assertTrue(shift)
        self.assertFalse(shift.shift_end)

        self.route.action_cancel_route()
        self.assertTrue(shift.exists())
        self.assertTrue(shift.shift_end)
        self.assertFalse(self.route.shift_id)
        self.assertEqual(self.route.state, 'to_start')
        for record in (self.route, shift):
            self.assertTrue(any(
                'closed by the cancellation' in (m.body or '') for m in record.message_ids),
                record._name)

    def test_cancel_route_keeps_shift_used_by_other_active_route(self):
        start = fields.Datetime.now() - timedelta(hours=1)
        shift = self.env['wm.driver.shift'].create({
            'driver_id': self.driver.id,
            'vehicle_id': self.vehicle.id,
            'shift_start': start,
        })
        other = self.env['wm.route'].create({
            'date': self.today, 'vehicle_id': self._vehicle('DEC-OTHER').id, 'driver_id': self.driver.id,
        })
        for route in (self.route, other):
            route.with_context(programmatic_state_change=True).write({
                'state': 'running', 'actual_start': start, 'shift_id': shift.id,
            })
        self.route.action_cancel_route()
        self.assertTrue(shift.exists())
        self.assertFalse(shift.shift_end)
        self.assertEqual(shift.route_ids, other)

    # Decision 7: pre-trip checklist valid since the vehicle's last route ----
    def test_old_checklist_counts_when_vehicle_never_ran(self):
        vehicle = self._vehicle('DEC-NEW')
        self._checklist(vehicle, self.today - timedelta(days=10))
        route = self.env['wm.route'].create({'date': self.today + timedelta(days=1), 'vehicle_id': vehicle.id})
        self.assertTrue(route.is_inspected)

    def test_checklist_invalidated_by_vehicle_route_start(self):
        """Starting a route consumes the checklist for the vehicle's other open routes."""
        tomorrow = self.today + timedelta(days=1)
        next_route = self.env['wm.route'].create({'date': tomorrow, 'vehicle_id': self.vehicle.id})
        self.assertTrue(next_route.is_inspected)

        self._mark_started(self.route, self._just_started())
        self.assertFalse(next_route.is_inspected)
        self.assertFalse(next_route.is_ready_to_dispatch)

        # A new checklist checked after that start re-validates the route.
        checklist = self._checklist(self.vehicle, tomorrow, state='tocheck')
        self.assertFalse(next_route.is_inspected)
        checklist.state = 'checked'
        self.assertTrue(next_route.is_inspected)

        # Completing the route keeps it the vehicle's last run.
        self._mark_started(self.route, self.route.actual_start, state='completed')
        self.assertTrue(next_route.is_inspected)

    def test_checklist_after_previous_completed_route_counts(self):
        vehicle = self._vehicle('DEC-HIST')
        previous = self.env['wm.route'].create({'date': self.today - timedelta(days=5), 'vehicle_id': vehicle.id})
        self._mark_started(previous, datetime.combine(self.today - timedelta(days=5), time(8, 0)), 'completed')
        self._checklist(vehicle, self.today - timedelta(days=6))
        route = self.env['wm.route'].create({'date': self.today, 'vehicle_id': vehicle.id})
        self.assertFalse(route.is_inspected, "A checklist from before the last route must not count.")
        self._checklist(vehicle, self.today - timedelta(days=3))
        self.assertTrue(route.is_inspected, "A checklist done since the last route stays valid.")

    def test_cancelled_route_start_no_longer_consumes_checklist(self):
        """A cancelled start is not a run: the vehicle's other routes are inspected again."""
        tomorrow = self.today + timedelta(days=1)
        next_route = self.env['wm.route'].create({'date': tomorrow, 'vehicle_id': self.vehicle.id})
        self._mark_started(self.route, self._just_started())
        self.assertFalse(next_route.is_inspected)
        self.route.action_cancel_route()
        self.assertTrue(next_route.is_inspected)

    # Decision 9: failed manifest disposal does not abort gate processing ---
    def test_gate_entry_survives_manifest_dispose_error(self):
        if 'wm.compliance.manifest' not in self.env or 'wm.compliance.custody' not in self.env:
            self.skipTest("wm_compliance is not installed")
        facility = self.env['wm.disposal.facility'].create({
            'name': 'Dec Treatment Plant', 'facility_type': 'treatment', 'license_no': 'DEC-LIC-1',
        })
        transporter = self.env['res.partner'].create({'name': 'Dec Transporter'})
        manifest = self.env['wm.compliance.manifest'].create({
            'generator_id': self.partner.id,
            'transporter_id': transporter.id,
            'disposal_facility_id': facility.id,
        })
        manifest.sudo().with_context(bypass_compliance_lock=True).write({'state': 'collected'})
        order = self._order(datetime.combine(self.today, time(9, 0)), state='completed')
        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': facility.id,
            'vehicle_id': self.vehicle.id,
            'collection_order_id': order.id,
            'confirmed_weight': 1000.0,
            'estimated_weight': 1000.0,
        })
        entry.action_start_weighing()
        Manifest = type(self.env['wm.compliance.manifest'])
        with patch.object(Manifest, 'action_dispose', autospec=True,
                          side_effect=UserError("Cannot dispose a manifest with zero quantity.")):
            entry.action_process_reconciliation()
        self.assertEqual(entry.state, 'accepted')
        self.assertEqual(manifest.state, 'collected')
        self.assertTrue(any('zero quantity' in (m.body or '') for m in entry.message_ids))

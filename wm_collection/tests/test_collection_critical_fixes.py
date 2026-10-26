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

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_collection')
class TestCollectionCriticalFixes(TransactionCase):
    """Regression tests for route dispatch scope, retries, schedules, batches and gate entries."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.context_today(cls.env.user)
        cls.category = cls.env['wm.waste.category'].create({'name': 'Fix Cardboard', 'code': 'FXCARD'})
        cls.product = cls.env['product.product'].create({
            'name': 'Fix Cardboard Waste',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Fix Generator'})
        cls.driver = cls.env['res.partner'].create({'name': 'Fix Driver'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Fix Bay', 'partner_id': cls.partner.id})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Fix Trucks'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Fix Hauler', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': model.id, 'license_plate': 'FIX-001'})
        cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-TRIP-FIX',
            'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip',
            'state': 'checked',
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

    def test_dispatch_only_takes_orders_due_on_route_date(self):
        """Dispatching a route leaves future orders and other routes' orders at its points alone."""
        today_order = self._order(datetime.combine(self.today, time(10, 0)))
        future_order = self._order(datetime.combine(self.today + timedelta(days=7), time(10, 0)))
        other_route = self.env['wm.route'].create({'date': self.today})
        other_order = self._order(datetime.combine(self.today, time(11, 0)), route_id=other_route.id)

        self.route.action_dispatch_route()

        self.assertEqual(today_order.state, 'dispatched')
        self.assertEqual(today_order.route_id, self.route)
        self.assertEqual(future_order.state, 'draft')
        self.assertFalse(future_order.route_id)
        self.assertEqual(other_order.route_id, other_route)
        self.assertEqual(other_order.state, 'draft')

    def test_missed_retry_order_is_unrouted(self):
        """The retry order of a missed collection is not left on the original route."""
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_missed_collection', 'True')
        order = self._order(datetime.combine(self.today, time(10, 0)), route_id=self.route.id)
        reason = self.env['wm.missed.reason'].create({'name': 'Fix Blocked Gate'})
        self.env['wm.mark.missed.wizard'].create({'order_id': order.id, 'reason_id': reason.id}).action_confirm()
        self.assertTrue(order.retry_order_id)
        self.assertFalse(order.retry_order_id.route_id)

    def test_schedule_creates_route_per_occurrence(self):
        """A recurring schedule creates a dated route per run instead of reusing a past route."""
        template = self.env['wm.route'].create({
            'date': self.today - timedelta(days=7),
            'vehicle_id': self.vehicle.id,
            'line_ids': [(0, 0, {'collection_point_id': self.point.id, 'sequence': 10})],
        })
        run_dt = fields.Datetime.now() - timedelta(minutes=5)
        schedule = self.env['wm.schedule'].create({
            'name': 'Fix Weekly',
            'route_id': template.id,
            'recurrence': 'weekly',
            'next_run_date': run_dt - timedelta(days=14),  # two missed occurrences
        })

        self.env['wm.schedule']._process_schedules()

        orders = self.env['wm.collection.order'].search([('collection_point_id', '=', self.point.id),
                                                          ('route_id.date', '=', fields.Datetime.context_timestamp(schedule, run_dt).date())])
        self.assertEqual(len(orders), 1, "Only the latest due occurrence is generated")
        self.assertNotEqual(orders.route_id, template)
        self.assertFalse(template.collection_order_ids)
        self.assertGreater(schedule.next_run_date, fields.Datetime.now())

    def test_category_batch_merge_not_doubled(self):
        """Re-running batch creation on an order merged into a shared batch adds nothing."""
        start = datetime.combine(self.today, time(9, 0))
        first = self._order(start, state='completed')
        second = self._order(start + timedelta(hours=2), state='completed')
        batch = first.action_create_category_batches()
        merged = second.action_create_category_batches()
        self.assertEqual(merged, batch)
        weight = batch.intake_weight
        self.assertEqual(second.waste_batch_count, 1)

        again = second.action_create_category_batches()
        self.assertEqual(again, batch)
        self.assertEqual(batch.intake_weight, weight)

    def test_failed_inspection_of_unreceived_batch_moves_no_stock(self):
        """Failing an inspection before receipt disposes the batch without a stock picking."""
        order = self._order(datetime.combine(self.today, time(9, 0)), state='completed')
        batch = order.action_create_category_batches()
        self.assertFalse(batch.is_received)
        pickings_before = self.env['stock.picking'].search_count([('origin', '=', batch.name)])
        inspection = self.env['wm.batch.inspection'].create({'batch_id': batch.id})
        inspection.action_fail_inspection()
        self.assertEqual(batch.status, 'disposed')
        self.assertEqual(self.env['stock.picking'].search_count([('origin', '=', batch.name)]), pickings_before)

    def test_gate_entry_reprocess_and_route_rejection(self):
        """Gate entries never bill the driver, never bill twice, and skip already-batched orders."""
        if 'wm.billable.event' not in self.env:
            self.skipTest("Billing module not installed")
        facility = self.env['wm.disposal.facility'].create({'name': 'Fix Plant', 'facility_type': 'treatment'})
        Event = self.env['wm.billable.event']

        # Load without an order, with rejected weight: nobody to bill but the driver -> no event
        route_entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': facility.id,
            'vehicle_id': self.vehicle.id,
            'confirmed_weight': 5000.0,
            'accepted_weight': 4000.0,
            'rejected_weight': 1000.0,
        })
        route_entry.action_process_reconciliation()
        self.assertFalse(Event.search([('gate_entry_id', '=', route_entry.id), ('partner_id', '=', self.driver.id)]))

        # Order-level load: contamination billed once, even after reset + re-processing
        order = self._order(datetime.combine(self.today, time(9, 0)), state='completed')
        order.action_create_category_batches()
        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': facility.id,
            'vehicle_id': self.vehicle.id,
            'collection_order_id': order.id,
            'confirmed_weight': 5000.0,
            'accepted_weight': 4000.0,
            'rejected_weight': 1000.0,
        })
        entry.action_process_reconciliation()
        entry.action_reset_draft()
        entry.action_process_reconciliation()
        self.assertEqual(Event.search_count([('gate_entry_id', '=', entry.id), ('event_type', '=', 'contamination')]), 1)
        # The order was already batched on completion: no INTAKE batch on top
        self.assertFalse(self.env['waste.batch'].search([('name', '=like', 'INTAKE/%s%%' % entry.name)]))

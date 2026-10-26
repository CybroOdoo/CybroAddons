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
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.wm_collection.models.wm_vehicle_maintenance_checklist import (
    _FAILED_ANSWER_RE,
)


@tagged('post_install', '-at_install', 'wm_collection')
class TestCollectionMediumFixes(TransactionCase):
    """Regression tests for the medium-severity wm_collection fixes (C-13 .. C-24)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.context_today(cls.env.user)
        cls.category = cls.env['wm.waste.category'].create({'name': 'Med Cardboard', 'code': 'MEDCARD'})
        cls.product = cls.env['product.product'].create({
            'name': 'Med Cardboard Waste',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Med Generator'})
        cls.driver = cls.env['res.partner'].create({'name': 'Med Driver'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Med Bay', 'partner_id': cls.partner.id})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Med Trucks'})
        cls.vmodel = cls.env['fleet.vehicle.model'].create({'name': 'Med Hauler', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': cls.vmodel.id, 'license_plate': 'MED-001'})
        cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-TRIP-MED',
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

    def _in_progress_order(self, actual_start, **vals):
        order = self._order(actual_start, **vals)
        order.with_context(programmatic_state_change=True).write({
            'state': 'in_progress',
            'actual_start': actual_start,
        })
        return order

    # C-13 ------------------------------------------------------------------
    def test_offline_completion_time_is_kept(self):
        """A synced 'completed' log keeps the device time as actual end."""
        start = fields.Datetime.now() - timedelta(hours=3)
        order = self._in_progress_order(start)
        done_at = start + timedelta(hours=1)
        self.env['wm.collection.order.status.log'].create({
            'order_id': order.id, 'status': 'completed', 'timestamp': done_at,
        })
        self.assertEqual(order.state, 'completed')
        self.assertEqual(order.actual_end, done_at)

    def test_completion_log_before_start_is_clamped(self):
        """A completion timestamp before the start is clamped instead of crashing."""
        start = fields.Datetime.now() - timedelta(hours=1)
        order = self._in_progress_order(start)
        self.env['wm.collection.order.status.log'].create({
            'order_id': order.id, 'status': 'completed', 'timestamp': start - timedelta(minutes=10),
        })
        self.assertEqual(order.state, 'completed')
        self.assertEqual(order.actual_end, start + timedelta(seconds=1))

    # C-14 ------------------------------------------------------------------
    def test_post_trip_checklist_only_for_unrouted_orders(self):
        """Routed order completion does not create a post-trip checklist; standalone does."""
        Checklist = self.env['wm.vehicle.maintenance.checklist']
        domain = [('vehicle_id', '=', self.vehicle.id), ('checklist_type', '=', 'post_trip')]
        start = fields.Datetime.now() - timedelta(hours=2)
        routed = self._in_progress_order(start, route_id=self.route.id, vehicle_id=self.vehicle.id)
        before = Checklist.search_count(domain)
        routed.action_complete()
        self.assertEqual(Checklist.search_count(domain), before)

        standalone = self._in_progress_order(start, vehicle_id=self.vehicle.id)
        standalone.action_complete()
        self.assertEqual(Checklist.search_count(domain), before + 1)

    # C-15 ------------------------------------------------------------------
    def test_cancel_dispatched_route_resets_orders(self):
        """Cancelling a dispatched route puts its dispatched orders back to draft."""
        order = self._order(datetime.combine(self.today, time(10, 0)), route_id=self.route.id)
        self.route.action_dispatch_route()
        self.assertEqual(order.state, 'dispatched')
        self.route.action_cancel_route()
        self.assertEqual(self.route.state, 'to_start')
        self.assertEqual(order.state, 'draft')

    def test_cancel_running_route_releases_shift(self):
        """Cancelling a started route closes (never deletes) its shift, drops the start time, keeps worked orders."""
        dispatched = self._order(datetime.combine(self.today, time(10, 0)), route_id=self.route.id)
        working = self._order(datetime.combine(self.today, time(11, 0)), route_id=self.route.id)
        self.route.action_dispatch_route()
        self.route.action_start_route()
        shift = self.route.shift_id
        self.assertTrue(shift)
        working.with_context(programmatic_state_change=True).write({'state': 'in_progress'})

        self.route.action_cancel_route()
        self.assertEqual(self.route.state, 'to_start')
        self.assertFalse(self.route.actual_start)
        self.assertFalse(self.route.shift_id)
        self.assertTrue(shift.exists())
        self.assertTrue(shift.shift_end)
        self.assertEqual(dispatched.state, 'draft')
        self.assertEqual(working.state, 'in_progress')

    # C-16 ------------------------------------------------------------------
    def test_inspection_fallback_is_same_day_and_recomputed(self):
        """A checklist done before the vehicle's last route does not inspect a
        later route; one done since that route does."""
        tomorrow = self.today + timedelta(days=1)
        route = self.env['wm.route'].create({'date': tomorrow, 'vehicle_id': self.vehicle.id})
        self.assertTrue(route.is_inspected)
        self.route.with_context(programmatic_state_change=True).write({
            'state': 'running', 'actual_start': fields.Datetime.now() + timedelta(seconds=1),
        })
        self.assertFalse(route.is_inspected)
        self.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'PRE-TRIP-MED-TMRW',
            'vehicle_id': self.vehicle.id,
            'checklist_type': 'pre_trip',
            'state': 'checked',
            'date': tomorrow,
        })
        self.assertTrue(route.is_inspected)

    # C-17 ------------------------------------------------------------------
    def test_failed_answer_matching_is_whole_word(self):
        """'Normal' / 'Not applicable' are not failures; 'No' / 'Failed' are."""
        for ok in ('Normal', 'Not applicable', 'Good', 'Yes'):
            self.assertFalse(_FAILED_ANSWER_RE.search(ok), ok)
        for bad in ('No', 'no leaks found? no', 'Failed', 'Defective', 'damaged'):
            self.assertTrue(_FAILED_ANSWER_RE.search(bad), bad)

    def test_standby_vehicle_skips_busy_vehicles(self):
        """Standby selection excludes vehicles on another open route that day."""
        busy = self.env['fleet.vehicle'].create({'model_id': self.vmodel.id, 'license_plate': 'MED-BUSY'})
        self.env['wm.route'].create({'date': self.today, 'vehicle_id': busy.id})
        free = self.env['fleet.vehicle'].create({'model_id': self.vmodel.id, 'license_plate': 'MED-FREE'})
        standby = self.env['survey.user_input']._find_standby_vehicle(self.vehicle, self.route)
        self.assertTrue(standby)
        self.assertNotEqual(standby, busy)
        self.assertNotEqual(standby, self.vehicle)
        busy_ids = self.env['wm.route'].search([
            ('date', '=', self.today), ('state', '!=', 'completed'), ('id', '!=', self.route.id),
        ]).vehicle_id
        self.assertNotIn(standby, busy_ids)
        self.assertTrue(free)

    # C-18 ------------------------------------------------------------------
    def test_consolidated_sort_merges_same_destination_product(self):
        """Two materials sorted into one destination product give one child line."""
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        products = self.env['product.product']
        for i in range(2):
            tmpl = self.env['product.template'].create({
                'name': f'Med Mix {i}', 'is_waste_material': True,
                'wm_waste_category_id': self.category.id, 'is_storable': True,
            })
            products |= tmpl.product_variant_id
        batch = self.env['waste.batch'].create({
            'warehouse_id': warehouse.id,
            'location_id': warehouse.lot_stock_id.id,
            'category_id': self.category.id,
            'line_ids': [(0, 0, {'product_id': p.id, 'quantity': 100.0}) for p in products],
        })
        batch.with_context(skip_inspection_check=True).action_receive_batch()
        batch.with_context(skip_inspection_check=True).action_move_to_stock()
        dest_product = products[0]
        lines_data = [
            {'batch_line': line, 'sort_qty': qty, 'dest_product': dest_product}
            for line, qty in zip(batch.line_ids, (30.0, 20.0))
        ]
        child = batch._execute_grouped_sort_moves(lines_data, warehouse.lot_stock_id)
        self.assertEqual(len(child.line_ids), 1)
        self.assertEqual(child.line_ids.product_id, dest_product)
        self.assertAlmostEqual(child.line_ids.quantity, 50.0)

    # C-19 ------------------------------------------------------------------
    def test_latest_inspection_wins(self):
        """A failed re-inspection after a pass makes the batch 'failed'."""
        batch = self.env['waste.batch'].create({'category_id': self.category.id})
        now = fields.Datetime.now()
        Inspection = self.env['wm.batch.inspection']
        Inspection.create({'batch_id': batch.id, 'state': 'passed', 'inspection_date': now - timedelta(hours=2)})
        self.assertEqual(batch.inspection_state, 'passed')
        Inspection.create({'batch_id': batch.id, 'state': 'failed', 'inspection_date': now})
        self.assertEqual(batch.inspection_state, 'failed')

    # C-20 ------------------------------------------------------------------
    def test_manual_price_survives_completion(self):
        """A manually entered line price is not reset when the order completes."""
        self.product.list_price = 3.0
        order = self._in_progress_order(fields.Datetime.now() - timedelta(hours=1))
        line = order.order_line_ids
        self.assertEqual(line.price, 3.0, "Rate pricing still applies on creation")
        line.price = 7.5
        order.action_complete()
        self.assertEqual(line.price, 7.5)

    # C-21 / C-22 -----------------------------------------------------------
    def test_zone_cron_uses_local_date_and_company(self):
        """Orders are grouped by local scheduled date and routes carry the order company."""
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_route_zones', 'True')
        self.env.user.tz = 'Asia/Kolkata'  # UTC+05:30
        zone = self.env['wm.service.zone'].create({'name': 'Med Zone'})
        point = self.env['wm.collection.point'].create({
            'name': 'Med Zone Bay', 'partner_id': self.partner.id, 'zone_id': zone.id,
        })
        # 20:00 UTC is already the next day in Kolkata.
        utc_start = datetime.combine(self.today, time(20, 0))
        order = self._order(utc_start, collection_point_id=point.id)
        self.env['wm.route']._cron_auto_assign_orders_to_routes()
        self.assertTrue(order.route_id)
        self.assertEqual(order.route_id.date, self.today + timedelta(days=1))
        self.assertEqual(order.route_id.company_id, order.company_id)

    def test_add_point_order_scheduled_at_local_nine(self):
        """A stop added to a route gets an order at 09:00 local time, stored in UTC."""
        self.env.user.tz = 'Asia/Kolkata'
        point = self.env['wm.collection.point'].create({'name': 'Med New Stop', 'partner_id': self.partner.id})
        self.route.action_add_collection_point(point.id, optimize=False)
        order = self.env['wm.collection.order'].search([('collection_point_id', '=', point.id)])
        self.assertEqual(order.scheduled_start, datetime.combine(self.route.date, time(3, 30)))

    # C-23 / X-19 -----------------------------------------------------------
    def _container(self, period, deployed_days_ago):
        ctype = self.env['wm.container.type'].create({
            'name': f'Med Bin {period}', 'code': f'MED{period[:3].upper()}', 'capacity_volume': 240.0,
        })
        container = self.env['wm.container'].create({
            'name': f'BIN-MED-{period}',
            'container_type_id': ctype.id,
            'collection_point_id': self.point.id,
            'rental_rate': 10.0,
            'rental_period': period,
        })
        container.deployed_date = self.today - timedelta(days=deployed_days_ago)
        return container

    def test_rental_invoice_bills_from_last_invoiced_date(self):
        """Daily rental is billed once per elapsed day, never re-billed from deployment."""
        container = self._container('daily', 10)
        action = container.action_create_rental_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.invoice_line_ids.quantity, 10.0)
        self.assertEqual(container.last_invoiced_date, fields.Date.today())
        with self.assertRaises(UserError):
            container.action_create_rental_invoice()

        container.last_invoiced_date = fields.Date.today() - timedelta(days=3)
        action = container.action_create_rental_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.invoice_line_ids.quantity, 3.0)

    def test_rental_invoice_requires_finance_rights(self):
        """A dispatcher cannot create rental invoices."""
        container = self._container('monthly', 5)
        user = self.env['res.users'].create({
            'name': 'Med Dispatcher',
            'login': 'med_dispatcher',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('wm_base.group_wm_dispatcher').id])],
        })
        with self.assertRaises(AccessError):
            container.with_user(user).action_create_rental_invoice()

    # C-24 ------------------------------------------------------------------
    def test_address_change_clears_stale_coordinates(self):
        """Changing the address drops old coordinates; explicit coordinates are kept."""
        point = self.env['wm.collection.point'].create({
            'name': 'Med Geo', 'partner_id': self.partner.id,
            'street': 'Old Street 1', 'latitude': 10.5, 'longitude': 76.2,
        })
        point.write({'street': 'New Street 2'})
        # Geocoding is unavailable in tests, so the stale pair is just cleared.
        self.assertFalse(point.latitude)
        self.assertFalse(point.longitude)

        point.write({'street': 'Third Street 3', 'latitude': 11.0, 'longitude': 77.0})
        self.assertEqual((point.latitude, point.longitude), (11.0, 77.0))

        point.write({'street': 'Third Street 3'})
        self.assertEqual((point.latitude, point.longitude), (11.0, 77.0))

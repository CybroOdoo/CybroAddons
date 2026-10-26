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

import pytz

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_collection')
class TestCollectionReviewFixes(TransactionCase):
    """Regression tests for the collection code-review findings: completion
    documents, manifest reuse, route vehicle changes, timezones, facility
    company scoping and batched billing rule lookups."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.context_today(cls.env.user)
        cls.category = cls.env['wm.waste.category'].create({'name': 'Rev Glass', 'code': 'REVGLS'})
        cls.category2 = cls.env['wm.waste.category'].create({'name': 'Rev Metal', 'code': 'REVMTL'})
        cls.product = cls.env['product.product'].create({
            'name': 'Rev Glass Waste', 'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
        })
        cls.product2 = cls.env['product.product'].create({
            'name': 'Rev Metal Waste', 'is_waste_material': True,
            'wm_waste_category_id': cls.category2.id,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Rev Generator'})
        cls.driver = cls.env['res.partner'].create({'name': 'Rev Driver'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Rev Bay', 'partner_id': cls.partner.id})
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Rev Trucks'})
        cls.vmodel = cls.env['fleet.vehicle.model'].create({'name': 'Rev Hauler', 'brand_id': brand.id})
        cls.vehicle = cls._vehicle('REV-001')

    @classmethod
    def _vehicle(cls, plate):
        return cls.env['fleet.vehicle'].create({'model_id': cls.vmodel.id, 'license_plate': plate})

    def _checklist(self, vehicle, date):
        return self.env['wm.vehicle.maintenance.checklist'].create({
            'name': f'PRE-TRIP-{vehicle.license_plate}-{date}',
            'vehicle_id': vehicle.id,
            'checklist_type': 'pre_trip',
            'state': 'checked',
            'date': date,
        })

    def _order(self, start=None, lines=None, **vals):
        start = start or datetime.combine(self.today, time(9, 0))
        lines = lines or [(self.category, self.product, 50.0)]
        return self.env['wm.collection.order'].create(dict({
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'scheduled_start': start,
            'scheduled_end': start + timedelta(hours=1),
            'order_line_ids': [(0, 0, {
                'category_id': cat.id, 'product_id': prod.id, 'weight': weight,
            }) for cat, prod, weight in lines],
        }, **vals))

    def _completed(self, order):
        order.with_context(programmatic_state_change=True).write({'state': 'completed'})
        return order

    # Finding 1: completion documents do not depend on compliance --------
    def test_completion_documents_without_compliance(self):
        """PDF, signature template and overweight event are produced on
        completion even when the manifest automation does nothing, for every
        order of a multi-record completion."""
        container_type = self.env['wm.container.type'].create({'name': 'Rev Bin', 'capacity_weight': 40.0})
        point = self.env['wm.collection.point'].create({
            'name': 'Rev Heavy Bay', 'partner_id': self.partner.id, 'container_id': container_type.id,
        })
        orders = self._order(collection_point_id=point.id) | self._order(
            start=datetime.combine(self.today, time(11, 0)), collection_point_id=point.id)
        Order = type(self.env['wm.collection.order'])
        with patch.object(Order, '_automate_compliance_manifest', autospec=True, return_value=None), \
                patch.object(Order, '_generate_collection_report_pdf', autospec=True,
                             side_effect=lambda rec: (b'%PDF-1.4 test', f'Collection_Order_{rec.name}.pdf')):
            orders.action_complete()

        template = self.env.ref('wm_collection.sig_template_collection_order', raise_if_not_found=False)
        for order in orders:
            self.assertEqual(order.state, 'completed')
            self.assertTrue(order.collection_report_pdf)
            self.assertEqual(order.collection_report_pdf_filename, f'Collection_Order_{order.name}.pdf')
            if template:
                self.assertEqual(order.signature_template_id, template)
            if 'wm.billable.event' in self.env:
                events = self.env['wm.billable.event'].search([
                    ('collection_order_id', '=', order.id), ('event_type', '=', 'overweight')])
                self.assertEqual(len(events), 1)
                self.assertAlmostEqual(events.quantity, 10.0)

    # Finding 3: manifest reuse ---------------------------------------------
    def _manifest_lines(self, order):
        return self.env['wm.compliance.manifest.line'].search([
            ('collection_order_id', '=', order.id)])

    def test_same_day_orders_both_on_manifests(self):
        """Two orders of one generator on one day both get their waste on a
        manifest (a new one once the first has left draft)."""
        if 'wm.compliance.manifest' not in self.env:
            self.skipTest("Compliance module not installed")
        self.env['wm.disposal.facility'].create({'name': 'Rev Plant', 'facility_type': 'landfill'})
        order1 = self._completed(self._order())
        order2 = self._completed(self._order(
            start=datetime.combine(self.today, time(14, 0)),
            lines=[(self.category, self.product, 30.0), (self.category2, self.product2, 20.0)]))
        order1._automate_compliance_manifest()
        order2._automate_compliance_manifest()

        lines1, lines2 = self._manifest_lines(order1), self._manifest_lines(order2)
        self.assertEqual(sorted(lines1.mapped('quantity')), [50.0])
        self.assertEqual(sorted(lines2.mapped('quantity')), [20.0, 30.0])
        self.assertEqual(set(lines2.mapped('waste_category_id').ids), {self.category.id, self.category2.id})
        for manifest in (lines1 | lines2).manifest_id:
            self.assertEqual(manifest.company_id, order1.company_id)
            self.assertEqual(manifest.generator_id, self.partner)

        # Called again: the order's lines are not added twice
        order2._automate_compliance_manifest()
        self.assertEqual(len(self._manifest_lines(order2)), 2)

    def test_draft_manifest_reused_and_extended(self):
        """A manifest still in draft (e.g. blocked on compliance codes) gets
        the next order's lines appended; non-draft manifests are not reused."""
        if 'wm.compliance.manifest' not in self.env:
            self.skipTest("Compliance module not installed")
        self.env['wm.disposal.facility'].create({'name': 'Rev Plant', 'facility_type': 'landfill'})
        Manifest = type(self.env['wm.compliance.manifest'])
        order1 = self._completed(self._order())
        order2 = self._completed(self._order(
            start=datetime.combine(self.today, time(14, 0)),
            lines=[(self.category2, self.product2, 25.0)]))
        with patch.object(Manifest, 'action_submit', autospec=True,
                          side_effect=UserError("Missing compliance codes")):
            order1._automate_compliance_manifest()
            order2._automate_compliance_manifest()
        manifest = self._manifest_lines(order1).manifest_id
        self.assertEqual(len(manifest), 1)
        self.assertEqual(manifest.state, 'draft')
        self.assertEqual(self._manifest_lines(order2).manifest_id, manifest)
        self.assertEqual(sorted(manifest.line_ids.mapped('quantity')), [25.0, 50.0])

        # Once submitted it is no longer extended
        manifest.sudo().with_context(bypass_compliance_lock=True).write({'state': 'submitted'})
        order3 = self._completed(self._order(start=datetime.combine(self.today, time(16, 0))))
        order3._automate_compliance_manifest()
        self.assertNotEqual(self._manifest_lines(order3).manifest_id, manifest)
        self.assertTrue(self._manifest_lines(order3))

    # Finding 7: vehicle change on routes ------------------------------------
    def test_route_vehicle_change_rules(self):
        """A to_start route covered only by the vehicle's checklist may switch
        vehicles; its own passed inspection or dispatch pins the vehicle."""
        vehicle_a, vehicle_b = self._vehicle('REV-VA'), self._vehicle('REV-VB')
        self._checklist(vehicle_a, self.today)
        route = self.env['wm.route'].create({
            'date': self.today, 'vehicle_id': vehicle_a.id, 'driver_id': self.driver.id,
            'line_ids': [(0, 0, {'collection_point_id': self.point.id, 'sequence': 10})],
        })
        self.assertTrue(route.is_inspected)
        route.write({'vehicle_id': vehicle_b.id})
        self.assertEqual(route.vehicle_id, vehicle_b)
        self.assertFalse(route.is_inspected)

        # The route's own passed pre-trip inspection pins the vehicle
        survey = self.env['survey.survey'].create({
            'title': 'Rev Pre-Trip', 'scoring_type': 'no_scoring', 'scoring_success_min': 0.0})
        self.env['survey.user_input'].create({
            'survey_id': survey.id, 'route_id': route.id,
            'checklist_type': 'pre_trip', 'state': 'done',
        })
        route.invalidate_recordset(['is_inspected', 'inspection_ids'])
        self.assertTrue(route.is_inspected)
        with self.assertRaises(UserError):
            route.write({'vehicle_id': vehicle_a.id})

        # Dispatched routes stay blocked
        route2 = self.env['wm.route'].create({
            'date': self.today, 'vehicle_id': vehicle_a.id, 'driver_id': self.driver.id,
            'line_ids': [(0, 0, {'collection_point_id': self.point.id, 'sequence': 10})],
        })
        route2.action_dispatch_route()
        self.assertEqual(route2.state, 'dispatched')
        with self.assertRaises(UserError):
            route2.write({'vehicle_id': vehicle_b.id})

    # Finding 8: route timezone -----------------------------------------------
    def test_route_orders_use_company_timezone(self):
        """Without a user timezone the company's is used to find the route
        day's orders; an invalid timezone falls back instead of crashing."""
        self.env.user.tz = False
        self.env.company.partner_id.tz = 'Pacific/Auckland'
        Route = self.env['wm.route']
        self.assertEqual(Route._get_wm_tz(self.env.company).zone, 'Pacific/Auckland')

        route_date = self.today + timedelta(days=1)
        vehicle = self._vehicle('REV-TZ')
        self._checklist(vehicle, self.today)
        route = Route.create({
            'date': route_date, 'vehicle_id': vehicle.id, 'driver_id': self.driver.id,
            'line_ids': [(0, 0, {'collection_point_id': self.point.id, 'sequence': 10})],
        })
        nz = pytz.timezone('Pacific/Auckland')
        local_9am = nz.localize(datetime.combine(route_date, time(9, 0))).astimezone(pytz.UTC).replace(tzinfo=None)
        unrouted = self._order(start=local_9am)
        # 9:00 in Auckland is still the previous day in UTC
        self.assertEqual(local_9am.date(), route_date - timedelta(days=1))

        point2 = self.env['wm.collection.point'].create({'name': 'Rev TZ Bay', 'partner_id': self.partner.id})
        route.action_add_collection_point(point2.id, optimize=False)
        added = self.env['wm.collection.order'].search([('collection_point_id', '=', point2.id)])
        self.assertEqual(added.route_id, route)
        self.assertEqual(added.scheduled_start, local_9am)

        self.assertEqual(route._get_route_orders(('draft',)), unrouted | added)
        route.action_dispatch_route()
        self.assertEqual(unrouted.state, 'dispatched')
        self.assertEqual(unrouted.route_id, route)
        self.assertEqual(added.state, 'dispatched')

        # An invalid stored timezone name falls back to UTC
        self.env.flush_all()
        self.env.cr.execute("UPDATE res_partner SET tz = 'Not/AZone' WHERE id = %s",
                            [self.env.company.partner_id.id])
        self.env.invalidate_all()
        self.assertEqual(Route._get_wm_tz(self.env.company), pytz.UTC)

    # Finding 9: facility company scoping --------------------------------------
    def test_automation_uses_order_company_facility(self):
        """Gate entries and manifests only use a facility of the order's
        company; with none, they are skipped with a chatter note."""
        company_a = self.env['res.company'].create({'name': 'Rev Company A'})
        company_b = self.env['res.company'].create({'name': 'Rev Company B'})
        facility_b = self.env['wm.disposal.facility'].create({
            'name': 'Rev Plant B', 'facility_type': 'landfill', 'company_id': company_b.id})
        order = self._completed(self._order(vehicle_id=self.vehicle.id, company_id=company_a.id))
        self.assertEqual(order.company_id, company_a)

        GateEntry = self.env['wm.facility.gate.entry']
        order._automate_gate_entry()
        order._automate_compliance_manifest()
        self.assertFalse(GateEntry.search([('collection_order_id', '=', order.id)]))
        if 'wm.compliance.manifest' in self.env:
            self.assertFalse(self._manifest_lines(order))
            self.assertFalse(self.env['wm.compliance.manifest'].search([('disposal_facility_id', '=', facility_b.id)]))
        self.assertTrue(order.message_ids.filtered(lambda m: 'No disposal facility' in (m.body or '')))

        facility_a = self.env['wm.disposal.facility'].create({
            'name': 'Rev Plant A', 'facility_type': 'landfill', 'company_id': company_a.id})
        order._automate_gate_entry()
        self.assertEqual(GateEntry.search([('collection_order_id', '=', order.id)]).facility_id, facility_a)
        if 'wm.compliance.manifest' in self.env:
            order._automate_compliance_manifest()
            manifest = self._manifest_lines(order).manifest_id
            self.assertEqual(manifest.disposal_facility_id, facility_a)
            self.assertEqual(manifest.company_id, company_a)

    # Finding 10: batched billing rule lookups -----------------------------------
    def test_billing_rules_resolved_once_per_key(self):
        """Line prices are unchanged and the rate rule is looked up once per
        distinct (category, partner, date, contract), not once per line."""
        self.category.price = 2.5
        self.category2.price = 4.0
        order = self._order(lines=[
            (self.category, self.product, 10.0),
            (self.category2, self.product2, 5.0),
        ])
        product3 = self.env['product.product'].create({
            'name': 'Rev Glass Waste 2', 'is_waste_material': True,
            'wm_waste_category_id': self.category.id})
        self.env['wm.collection.order.line'].create({
            'order_id': order.id, 'category_id': self.category.id,
            'product_id': product3.id, 'weight': 4.0})
        lines = order.order_line_ids
        self.assertEqual(len(lines), 3)
        for line in lines:
            expected = line._get_billing_rule()
            unit = (expected.price if expected and expected.price else
                    line.product_id.list_price or line.category_id.price)
            if line.price_basis == 'per_kg':
                self.assertAlmostEqual(line.price, unit)

        Order = type(self.env['wm.collection.order'])
        with patch.object(Order, '_get_billing_rule', autospec=True,
                          side_effect=Order._get_billing_rule) as spy:
            rules = lines._get_billing_rules()
            self.assertEqual(spy.call_count, 2)
            self.assertEqual(set(rules), set(lines))
            spy.reset_mock()
            lines._compute_price()
            self.assertEqual(spy.call_count, 2)
            spy.reset_mock()
            lines._compute_price_basis()
            self.assertEqual(spy.call_count, 2)

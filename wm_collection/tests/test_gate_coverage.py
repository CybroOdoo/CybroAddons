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
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGateCoverage(TransactionCase):
    """Gate entry state guards, computes, constraints and downstream triggers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.facility = cls.env['wm.disposal.facility'].create({
            'name': 'Coverage Plant',
            'facility_type': 'treatment',
            'license_no': 'COV-PERMIT-1',
            'company_id': cls.env.company.id,
        })
        brand = cls.env['fleet.vehicle.model.brand'].search([], limit=1) or \
            cls.env['fleet.vehicle.model.brand'].create({'name': 'Cov Haulers'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Cov Hauler', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({'license_plate': 'COV-100', 'model_id': model.id})
        cls.partner = cls.env['res.partner'].create({'name': 'Coverage Client'})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Cov Gate Cat', 'code': 'COV-GATE'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Cov Site', 'partner_id': cls.partner.id})
        cls.Gate = cls.env['wm.facility.gate.entry']

    def _entry(self, **kw):
        vals = {'facility_id': self.facility.id, 'vehicle_id': self.vehicle.id}
        vals.update(kw)
        return self.Gate.create(vals)

    def _order(self, **kw):
        vals = {
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
        }
        vals.update(kw)
        return self.env['wm.collection.order'].create(vals)

    # ---- state guards ----
    def test_start_weighing_guard(self):
        entry = self._entry()
        entry.action_start_weighing()
        self.assertEqual(entry.state, 'in_progress')
        with self.assertRaises(UserError):
            entry.action_start_weighing()

    def test_process_reconciliation_guards(self):
        entry = self._entry()
        with self.assertRaises(ValidationError):
            entry.action_process_reconciliation()  # no weight
        entry.confirmed_weight = 600.0
        entry.action_process_reconciliation()
        self.assertEqual(entry.state, 'accepted')
        self.assertEqual(entry.accepted_weight, 600.0)
        with self.assertRaises(UserError):
            entry.action_process_reconciliation()  # already processed

    def test_cancel_and_reset_guards(self):
        entry = self._entry()
        with self.assertRaises(UserError):
            entry.action_reset_draft()  # draft
        entry.action_cancel()
        self.assertEqual(entry.state, 'cancelled')
        with self.assertRaises(UserError):
            entry.action_cancel()
        entry.action_reset_draft()
        self.assertEqual(entry.state, 'draft')

        accepted = self._entry(confirmed_weight=500.0)
        accepted.action_process_reconciliation()
        with self.assertRaises(UserError):
            accepted.action_cancel()
        with self.assertRaises(UserError):
            accepted.action_reset_draft()

    def test_rejected_and_partially_rejected_flow(self):
        order = self._order()
        rejected = self._entry(collection_order_id=order.id, confirmed_weight=500.0)
        self.env['wm.facility.gate.entry.rejection.line'].create({
            'gate_entry_id': rejected.id, 'collection_point_id': self.point.id, 'rejected_weight': 500.0,
        })
        # confirmed 500, all rejected -> accepted 0
        rejected.action_process_reconciliation()
        self.assertEqual(rejected.state, 'rejected')
        # may be cancelled / reset (not accepted)
        rejected.action_reset_draft()
        self.assertEqual(rejected.state, 'draft')
        rejected.action_cancel()
        self.assertEqual(rejected.state, 'cancelled')

    # ---- constraints ----
    def test_negative_weight_constraint(self):
        with self.assertRaises(ValidationError):
            self._entry(confirmed_weight=-5.0)

    def test_cancelled_entry_frees_collection_order(self):
        order = self._order()
        first = self._entry(collection_order_id=order.id)
        first.action_cancel()
        second = self._entry(collection_order_id=order.id)
        self.assertTrue(second.id)

    # ---- computes ----
    def test_confirmed_weight_from_order_and_editable(self):
        order = self._order(order_line_ids=[(0, 0, {'category_id': self.category.id, 'weight': 321.0})])
        entry = self._entry(collection_order_id=order.id)
        self.assertEqual(entry.confirmed_weight, 321.0)
        entry.confirmed_weight = 600.0
        self.assertEqual(entry.confirmed_weight, 600.0)
        manual = self._entry(confirmed_weight=250.0)
        self.assertEqual(manual.confirmed_weight, 250.0)

    def test_estimated_weight_from_lines(self):
        entry = self._entry()
        self.env['wm.facility.gate.entry.line'].create([
            {'gate_entry_id': entry.id, 'waste_category_id': self.category.id,
             'estimated_weight': 100.0, 'accepted_weight': 90.0, 'rejected_weight': 10.0},
            {'gate_entry_id': entry.id, 'waste_category_id': self.category.id,
             'estimated_weight': 50.0, 'accepted_weight': 50.0},
        ])
        self.assertEqual(entry.estimated_weight, 150.0)
        self.assertEqual(entry.accepted_weight, 140.0)
        self.assertEqual(entry.rejected_weight, 10.0)
        self.assertEqual(entry.reconciliation_status, 'rejected_items')

    def test_route_counts_gate_entries_of_its_orders(self):
        route = self.env['wm.route'].create({
            'name': 'Cov Route', 'date': '2026-09-30',
            'line_ids': [(0, 0, {'collection_point_id': self.point.id, 'sequence': 10})],
        })
        entry = self._entry(collection_order_id=self._order(route_id=route.id).id)
        self._entry()  # not on the route
        route.invalidate_recordset(['gate_entry_count'])
        self.assertEqual(route.gate_entry_count, 1)
        domain = route.action_view_gate_entries()['domain']
        self.assertEqual(self.Gate.search(domain), entry)

    def test_allowed_collection_points_from_order(self):
        order = self._order()
        entry = self._entry(collection_order_id=order.id)
        self.assertEqual(entry.allowed_collection_point_ids, self.point)
        self.assertFalse(self._entry().allowed_collection_point_ids)

    def test_reconciliation_status_thresholds(self):
        # the weight confirmed at the gate is compared with the order's confirmed weight
        order = self._order(order_line_ids=[(0, 0, {'category_id': self.category.id, 'weight': 1000.0})])
        under = self._entry(collection_order_id=order.id, confirmed_weight=600.0)
        self.assertEqual(under.weight_variance, -400.0)
        self.assertEqual(under.reconciliation_status, 'underweight')
        balanced = self._entry(
            collection_order_id=self._order(
                order_line_ids=[(0, 0, {'category_id': self.category.id, 'weight': 600.0})]).id,
            confirmed_weight=600.0)
        self.assertEqual(balanced.reconciliation_status, 'balanced')

    # ---- downstream triggers ----
    def test_reprocessing_does_not_duplicate_batches_or_events(self):
        order = self._order()
        entry = self._entry(collection_order_id=order.id, confirmed_weight=600.0)
        entry.action_process_reconciliation()
        batches = self.env['waste.batch'].search([('name', '=like', 'INTAKE/%s%%' % entry.name)])
        self.assertEqual(len(batches), 1)
        entry._trigger_inventory_intake()
        self.assertEqual(
            self.env['waste.batch'].search_count([('name', '=like', 'INTAKE/%s%%' % entry.name)]), 1)
        if 'wm.billable.event' in self.env:
            before = self.env['wm.billable.event'].search_count([('gate_entry_id', '=', entry.id)])
            entry._trigger_billing_events()
            self.assertEqual(
                self.env['wm.billable.event'].search_count([('gate_entry_id', '=', entry.id)]), before)

    def test_inventory_intake_per_line(self):
        entry = self._entry(confirmed_weight=600.0)
        cat2 = self.env['wm.waste.category'].create({'name': 'Cov Gate Cat 2', 'code': 'COV-GATE2'})
        self.env['wm.facility.gate.entry.line'].create([
            {'gate_entry_id': entry.id, 'waste_category_id': self.category.id, 'accepted_weight': 200.0},
            {'gate_entry_id': entry.id, 'waste_category_id': cat2.id, 'accepted_weight': 300.0},
            {'gate_entry_id': entry.id, 'waste_category_id': cat2.id, 'accepted_weight': 0.0},
        ])
        entry.action_process_reconciliation()
        batches = self.env['waste.batch'].search([('name', '=like', 'INTAKE/%s/%%' % entry.name)])
        self.assertEqual(len(batches), 2)
        self.assertEqual(sorted(batches.mapped('gross_weight')), [200.0, 300.0])

    def test_view_actions_and_feature_toggle(self):
        entry = self._entry()
        self.assertEqual(self.facility.action_view_gate_entries()['res_model'], 'wm.facility.gate.entry')
        self.assertEqual(entry.billable_event_count, 0)
        self.assertEqual(self.facility.gate_entry_count, 1)
        self.env['ir.config_parameter'].sudo().set_param('wm_collection.use_facility_gate_entry', 'False')
        with self.assertRaises(UserError):
            self.facility.action_view_gate_entries()
        with self.assertRaises(UserError):
            self._entry()

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
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFacilityGateEntry(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.facility = cls.env['wm.disposal.facility'].create({
            'name': 'EcoDump Processing Plant',
            'facility_type': 'treatment',
            'license_no': 'EPA-PERMIT-998877',
            'company_id': cls.company.id,
        })
        brand = cls.env['fleet.vehicle.model.brand'].search([], limit=1) or cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Haulers'})
        model = cls.env['fleet.vehicle.model'].create({'name': 'Heavy Hauler', 'brand_id': brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'license_plate': 'WM-TEST-100',
            'model_id': model.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Industrial Client',
        })
        cls.driver = cls.env['res.partner'].create({
            'name': 'Dave Driver',
        })
        cls.waste_category = cls.env['wm.waste.category'].create({
            'name': 'Hazardous Waste Sludge Gate Test',
            'code': 'HAZ-SLUDGE-GATE-TEST',
        })
        cls.collection_point = cls.env['wm.collection.point'].create({
            'name': 'Plant Site A',
            'partner_id': cls.partner.id,
        })
        cls.collection_order = cls.env['wm.collection.order'].create({
            'partner_id': cls.partner.id,
            'collection_point_id': cls.collection_point.id,
            'order_line_ids': [(0, 0, {'category_id': cls.waste_category.id})],
            'scheduled_start': '2026-09-25 08:00:00',
            'scheduled_end': '2026-09-25 10:00:00',
            'state': 'completed',
        })

    def test_01_gate_entry_confirmed_weight(self):
        """Test sequence generation and the confirmed weight entered at the gate."""
        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': self.facility.id,
            'vehicle_id': self.vehicle.id,
            'driver_id': self.driver.id,
            'collection_order_id': self.collection_order.id,
            'confirmed_weight': 12000.0,
        })
        self.assertTrue(entry.name.startswith('GATE/'))
        self.assertEqual(entry.confirmed_weight, 12000.0)
        self.assertEqual(entry.state, 'draft')

    def test_02_reconciliation_balanced_and_acceptance(self):
        """Test balanced reconciliation status and auto intake processing."""
        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': self.facility.id,
            'vehicle_id': self.vehicle.id,
            'collection_order_id': self.collection_order.id,
            'confirmed_weight': 10000.0,
            'estimated_weight': 10000.0,
        })
        self.assertEqual(entry.confirmed_weight, 10000.0)
        self.assertEqual(entry.reconciliation_status, 'balanced')

        # Action start weighing & reconciliation
        entry.action_start_weighing()
        self.assertEqual(entry.state, 'in_progress')

        entry.action_process_reconciliation()
        self.assertEqual(entry.state, 'accepted')
        self.assertEqual(entry.accepted_weight, 10000.0)
        self.assertTrue(entry.exit_datetime)

        # Verify waste.batch intake creation
        batches = self.env['waste.batch'].search([('collection_order_id', '=', self.collection_order.id)])
        self.assertTrue(len(batches) >= 1)

    def test_03_rejection_workflow_and_billing_trigger(self):
        """Test partial payload rejection creating contamination billable event."""
        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': self.facility.id,
            'vehicle_id': self.vehicle.id,
            'collection_order_id': self.collection_order.id,
            'confirmed_weight': 8000.0,
        })
        # Add payload line breakdown
        self.env['wm.facility.gate.entry.line'].create({
            'gate_entry_id': entry.id,
            'waste_category_id': self.waste_category.id,
            'estimated_weight': 8000.0,
            'accepted_weight': 6000.0,
            'rejected_weight': 2000.0,
            'rejection_reason': 'Prohibited medical waste contamination',
        })

        entry.action_process_reconciliation()
        self.assertEqual(entry.state, 'partially_rejected')
        self.assertEqual(entry.reconciliation_status, 'rejected_items')

        # Check contamination billable event auto-creation
        if 'wm.billable.event' in self.env:
            events = self.env['wm.billable.event'].search([('gate_entry_id', '=', entry.id)])
            self.assertTrue(len(events) >= 1)
            contamination_event = events.filtered(lambda e: e.event_type == 'contamination')
            self.assertEqual(contamination_event.quantity, 2000.0)
            self.assertEqual(contamination_event.partner_id, self.partner)

    def test_04_overweight_load_billing_trigger(self):
        """Test overweight load creating overweight billable event."""
        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': self.facility.id,
            'vehicle_id': self.vehicle.id,
            'collection_order_id': self.collection_order.id,
            'confirmed_weight': 15000.0,
            'estimated_weight': 10000.0,
        })
        self.assertEqual(entry.weight_variance, 5000.0)
        self.assertEqual(entry.reconciliation_status, 'overweight')

        entry.action_process_reconciliation()
        if 'wm.billable.event' in self.env:
            events = self.env['wm.billable.event'].search([
                ('gate_entry_id', '=', entry.id),
                ('event_type', '=', 'overweight')
            ])
            self.assertEqual(len(events), 1)
            self.assertEqual(events.quantity, 5000.0)

    def test_05_collection_order_onchange_payload_auto_populate(self):
        """Test onchange method auto-populating payload breakdown lines from order."""
        # Create order with order line
        category2 = self.env['wm.waste.category'].create({
            'name': 'Recyclable Plastic',
            'code': 'PLASTIC-REC',
        })
        order_with_lines = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'scheduled_start': '2026-09-26 08:00:00',
            'scheduled_end': '2026-09-26 10:00:00',
            'state': 'completed',
            'order_line_ids': [
                (0, 0, {
                    'category_id': self.waste_category.id,
                    'estimated_weight': 4000.0,
                }),
                (0, 0, {
                    'category_id': category2.id,
                    'estimated_weight': 2500.0,
                })
            ]
        })

        entry = self.env['wm.facility.gate.entry'].new({
            'facility_id': self.facility.id,
            'vehicle_id': self.vehicle.id,
        })
        entry.collection_order_id = order_with_lines
        entry._onchange_collection_order_id()

        self.assertEqual(len(entry.line_ids), 2)
        cats = entry.line_ids.mapped('waste_category_id')
        self.assertIn(self.waste_category, cats)
        self.assertIn(category2, cats)
        total_est = sum(entry.line_ids.mapped('estimated_weight'))
        self.assertEqual(total_est, 6500.0)

    def test_06_negative_confirmed_weight_constraint(self):
        """Test validation error when the Confirmed Weight is negative."""
        with self.assertRaises(ValidationError):
            self.env['wm.facility.gate.entry'].create({
                'facility_id': self.facility.id,
                'vehicle_id': self.vehicle.id,
                'confirmed_weight': -3000.0,
            })

    def test_07_unique_collection_order_constraint(self):
        """Test validation error when attempting to assign a collection order to multiple active gate entries."""
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'state': 'completed',
        })
        entry1 = self.env['wm.facility.gate.entry'].create({
            'facility_id': self.facility.id,
            'vehicle_id': self.vehicle.id,
            'collection_order_id': order.id,
        })
        self.assertTrue(entry1.id)

        # Attempting to assign same order to a second active entry must raise ValidationError
        with self.assertRaises(ValidationError):
            self.env['wm.facility.gate.entry'].create({
                'facility_id': self.facility.id,
                'vehicle_id': self.vehicle.id,
                'collection_order_id': order.id,
            })

    def test_08_order_state_constraint(self):
        """Test validation error when attempting to assign a draft or in_progress order to a gate entry."""
        draft_order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'state': 'draft',
        })
        with self.assertRaises(ValidationError):
            self.env['wm.facility.gate.entry'].create({
                'facility_id': self.facility.id,
                'vehicle_id': self.vehicle.id,
                'collection_order_id': draft_order.id,
            })

    def test_09_itemized_rejection_and_collection_point_restriction(self):
        """Test itemized rejection billing to the customer and the collection point restriction to the order."""
        partner_c = self.env['res.partner'].create({'name': 'Partner C (Outside Client)'})
        point_c = self.env['wm.collection.point'].create({
            'name': 'Site C (Outside)',
            'partner_id': partner_c.id,
        })

        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': self.facility.id,
            'vehicle_id': self.vehicle.id,
            'collection_order_id': self.collection_order.id,
            'confirmed_weight': 15000.0,
        })

        # Only the order's collection point can be itemized
        self.assertEqual(entry.allowed_collection_point_ids, self.collection_point)

        # 1. Attempt adding Site C (not the order's point) -> Expect ValidationError
        with self.assertRaises(ValidationError):
            self.env['wm.facility.gate.entry.rejection.line'].create({
                'gate_entry_id': entry.id,
                'collection_point_id': point_c.id,
                'rejected_weight': 500.0,
            })

        # 2. Add an itemized rejection line for the order's site
        line_a = self.env['wm.facility.gate.entry.rejection.line'].create({
            'gate_entry_id': entry.id,
            'collection_point_id': self.collection_point.id,
            'rejected_weight': 300.0,
            'rejection_reason': 'Site A Wet Sludge Contamination',
        })

        self.assertEqual(entry.rejected_weight, 300.0)
        self.assertEqual(line_a.partner_id, self.partner)

        # Process reconciliation
        entry.action_process_reconciliation()

        # Check the billable event created for the customer if billing module installed
        if 'wm.billable.event' in self.env:
            events_a = self.env['wm.billable.event'].search([
                ('gate_entry_id', '=', entry.id),
                ('partner_id', '=', self.partner.id),
                ('event_type', '=', 'contamination'),
            ])
            self.assertEqual(len(events_a), 1)
            self.assertEqual(events_a.quantity, 300.0)

    def test_09_confirmed_weight_from_collection_order(self):
        """Test confirmed_weight computation on gate entry from linked collection order."""
        order = self.env['wm.collection.order'].create({
            'partner_id': self.partner.id,
            'collection_point_id': self.collection_point.id,
            'order_line_ids': [(0, 0, {'category_id': self.waste_category.id, 'weight': 750.0})],
            'scheduled_start': '2026-09-25 08:00:00',
            'scheduled_end': '2026-09-25 10:00:00',
            'state': 'completed',
        })
        self.assertEqual(order.confirmed_weight, 750.0)

        entry = self.env['wm.facility.gate.entry'].create({
            'facility_id': self.facility.id,
            'vehicle_id': self.vehicle.id,
            'collection_order_id': order.id,
        })
        self.assertEqual(entry.confirmed_weight, 750.0)

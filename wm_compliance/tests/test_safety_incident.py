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
from datetime import timedelta

from odoo import fields
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestSafetyIncident(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = cls.env['res.partner'].create({
            'name': 'Test Safety Driver',
            'email': 'safety_driver@example.com',
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Safety Brand'})
        vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Safety Model',
            'brand_id': brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'license_plate': 'TEST-SAFETY-01',
            'model_id': vehicle_model.id,
        })
        cls.route = cls.env['wm.route'].create({
            'name': 'Route Safety Test',
            'date': fields.Date.today(),
            'driver_id': cls.driver.id,
            'vehicle_id': cls.vehicle.id if cls.vehicle else False,
        })

    def test_01_safety_incident_creation_sequence(self):
        """Test sequence generation (SI/00001) and default fields."""
        incident = self.env['wm.safety.incident'].create({
            'incident_type': 'spill',
            'severity': 'moderate',
            'description': 'Hydraulic fluid spill during container loading.',
            'driver_id': self.driver.id,
            'vehicle_id': self.vehicle.id if self.vehicle else False,
            'route_id': self.route.id,
            'is_osha_recordable': True,
            'regulatory_report_required': True,
            'regulatory_deadline': fields.Date.today() + timedelta(days=7),
        })
        self.assertTrue(incident.name.startswith('SI/'))
        self.assertEqual(incident.state, 'draft')
        self.assertTrue(incident.is_osha_recordable)
        self.assertTrue(incident.regulatory_report_required)

    def test_02_safety_incident_lifecycle_transitions(self):
        """Test lifecycle state transitions (draft -> reported -> investigating -> closed)."""
        incident = self.env['wm.safety.incident'].create({
            'incident_type': 'injury',
            'severity': 'severe',
            'description': 'Driver sprained ankle stepping off vehicle footboard.',
            'driver_id': self.driver.id,
        })
        self.assertEqual(incident.state, 'draft')

        incident.action_report()
        self.assertEqual(incident.state, 'reported')

        incident.action_investigate()
        self.assertEqual(incident.state, 'investigating')

        incident.action_close()
        self.assertEqual(incident.state, 'closed')

        incident.action_reset_to_draft()
        self.assertEqual(incident.state, 'draft')

    def test_03_closed_incident_immutability(self):
        """Test that closed safety incidents cannot be modified directly."""
        from odoo.exceptions import UserError
        incident = self.env['wm.safety.incident'].create({
            'incident_type': 'near_miss',
            'severity': 'minor',
            'description': 'Near miss vehicle backing up.',
        })
        incident.action_report()
        incident.action_close()
        self.assertEqual(incident.state, 'closed')

        with self.assertRaises(UserError):
            incident.write({'is_osha_recordable': True})

    def test_04_atomic_multi_record_transition_validation(self):
        """Test that batch state transitions are atomic (all-or-nothing)."""
        from odoo.exceptions import UserError
        inc1 = self.env['wm.safety.incident'].create({
            'incident_type': 'spill',
            'description': 'Incident 1 reported.',
        })
        inc1.action_report()

        inc2 = self.env['wm.safety.incident'].create({
            'incident_type': 'injury',
            'description': 'Incident 2 investigating.',
        })
        inc2.action_investigate()

        inc3 = self.env['wm.safety.incident'].create({
            'incident_type': 'near_miss',
            'description': 'Incident 3 draft.',
        })

        batch = inc1 | inc2 | inc3

        # Inc3 is draft (cannot be closed directly). Closing batch must raise UserError and NOT close Inc1 or Inc2.
        with self.assertRaises(UserError):
            batch.action_close()

        self.assertEqual(inc1.state, 'reported')
        self.assertEqual(inc2.state, 'investigating')
        self.assertEqual(inc3.state, 'draft')

    def test_05_regulatory_deadline_constraint(self):
        """Test that regulatory_deadline is required when regulatory_report_required=True."""
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['wm.safety.incident'].create({
                'incident_type': 'spill',
                'description': 'Chemical spill without deadline.',
                'regulatory_report_required': True,
                'regulatory_deadline': False,
            })

#############################################################################
# pylint: disable=missing-module-docstring,unknown-option-value,too-few-public-methods,attribute-string-redundant,prefer-env-translation,duplicate-code,super-with-arguments,unused-argument,no-name-in-module,protected-access
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Unit test suite for Parking Management module."""
import os
from datetime import date, datetime, timedelta

from odoo.modules.module import get_module_path
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestParkingManagement(TransactionCase):
    """Comprehensive test case for Parking Management workflows and models."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and master records."""
        super().setUpClass()
        cls.module_path = get_module_path('odoo_parking_management')

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Parking Customer',
            'email': 'customer.parking@gmail.com',
            'phone': '+1234567890',
        })

        # Master Location
        cls.location = cls.env['location.details'].create({
            'name': 'Floor 1 Section A',
        })

        # Slot Type
        cls.slot_type = cls.env['slot.type'].create({
            'vehicle_type': 'Compact Car',
            'code': 'CAR-01',
            'allowed_park_duration': 6.0,
        })

        # Slot Details
        cls.slot = cls.env['slot.details'].create({
            'name': 'A-101',
            'code': 'SLOT-A101',
            'slot_type_id': cls.slot_type.id,
        })

        # Fleet Vehicle and Vehicle Details
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Toyota'})
        cls.vmodel = cls.env['fleet.vehicle.model'].create({
            'name': 'Camry',
            'brand_id': cls.brand.id,
        })
        cls.fleet_vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.vmodel.id,
            'license_plate': 'PARK-9999',
        })

        cls.vehicle = cls.env['vehicle.details'].create({
            'vehicle_name': 'Camry Sedan',
            'vehicle_id': cls.fleet_vehicle.id,
            'partner_id': cls.partner.id,
            'number_plate': 'PARK-9999',
            'ownership_type': 'outsider',
        })

    def test_01_module_structure_and_files(self):
        """Validate presence of required documentation and manifest."""
        self.assertTrue(os.path.isdir(self.module_path), "Module directory should exist.")
        manifest_file = os.path.join(self.module_path, '__manifest__.py')
        self.assertTrue(os.path.isfile(manifest_file), "__manifest__.py must exist.")
        readme_file = os.path.join(self.module_path, 'README.rst')
        self.assertTrue(os.path.isfile(readme_file), "README.rst must exist.")
        icon_file = os.path.join(self.module_path, 'static', 'description', 'icon.png')
        self.assertTrue(os.path.isfile(icon_file), "icon.png must exist.")
        desc_file = os.path.join(self.module_path, 'static', 'description', 'index.html')
        self.assertTrue(os.path.isfile(desc_file), "index.html must exist.")

    def test_02_slot_type_and_location(self):
        """Test slot type and location configuration records."""
        self.assertEqual(self.location.name, 'Floor 1 Section A')
        self.assertEqual(self.slot_type.display_name, 'Compact Car')
        self.assertEqual(self.slot_type.allowed_park_duration, 6.0)

    def test_03_slot_details(self):
        """Test slot details record creation and attributes."""
        self.assertEqual(self.slot.name, 'A-101')
        self.assertEqual(self.slot.code, 'SLOT-A101')
        self.assertEqual(self.slot.slot_type_id, self.slot_type)

    def test_04_vehicle_details(self):
        """Test vehicle details record with both member and outsider types."""
        self.assertEqual(self.vehicle.number_plate, 'PARK-9999')
        self.assertEqual(self.vehicle.ownership_type, 'outsider')

        member_vehicle = self.env['vehicle.details'].create({
            'vehicle_name': 'Member SUV',
            'vehicle_id': self.fleet_vehicle.id,
            'partner_id': self.partner.id,
            'number_plate': 'MEM-1111',
            'ownership_type': 'member',
        })
        self.assertEqual(member_vehicle.ownership_type, 'member')

    def test_05_member_slot_reservation(self):
        """Test slot reservation creation for a partner/member."""
        today = date.today()
        end_date = today + timedelta(days=30)
        reservation = self.env['member.slot.reservation'].create({
            'slot_id': self.slot.id,
            'partner_id': self.partner.id,
            'start_date': today,
            'end_date': end_date,
        })
        self.assertEqual(reservation.slot_id, self.slot)
        self.assertEqual(reservation.partner_id, self.partner)
        self.assertEqual(reservation.start_date, today)
        self.assertEqual(reservation.end_date, end_date)

    def test_06_parking_entry_public_lifecycle(self):
        """Test complete public parking entry lifecycle: check in, check out, duration, action."""
        entry = self.env['parking.entry'].create({
            'customer_type': 'public',
            'partner_id': self.partner.id,
            'vehicle_id': self.vehicle.id,
            'slot_type_id': self.slot_type.id,
            'slot_id': self.slot.id,
            'location_id': self.location.id,
            'parking_cost': 25.0,
        })

        self.assertNotEqual(entry.name, 'New')
        self.assertEqual(entry.state, 'draft')
        self.assertFalse(entry.check_in_bool)
        self.assertFalse(entry.check_out_bool)

        # Onchange slot type test
        domain_res = entry.onchange_slot_type_id()
        self.assertIn('slot_id', domain_res.get('domain', {}))

        # Check in
        entry.action_check_in()
        self.assertEqual(entry.state, 'check_in')
        self.assertTrue(entry.check_in_bool)
        self.assertFalse(entry.check_out_bool)
        self.assertTrue(entry.check_in)

        # Set specific check-in time and check-out time for duration calculation
        past_check_in = datetime.now() - timedelta(hours=2, minutes=30)
        entry.write({'check_in': past_check_in})
        entry.action_check_out()
        self.assertEqual(entry.state, 'check_out')
        self.assertTrue(entry.check_out_bool)
        self.assertFalse(entry.check_in_bool)
        self.assertTrue(entry.check_out)

        # Duration computation
        entry._compute_duration()
        self.assertTrue(entry.duration > 0)

        # Wizard action trigger
        act = entry.action_register_payment()
        self.assertEqual(act.get('res_model'), 'register.payment.wizard')
        self.assertEqual(act.get('context', {}).get('default_partner_id'), self.partner.id)
        self.assertEqual(act.get('context', {}).get('default_amount'), 25.0)

    def test_07_parking_entry_private_lifecycle(self):
        """Test private parking entry creation and sequence generation."""
        entry = self.env['parking.entry'].create({
            'customer_type': 'private',
            'partner_id': self.partner.id,
            'vehicle_id': self.vehicle.id,
            'slot_type_id': self.slot_type.id,
            'slot_id': self.slot.id,
            'location_id': self.location.id,
        })
        self.assertNotEqual(entry.name, 'New')
        self.assertEqual(entry.customer_type, 'private')

    def test_08_register_payment_wizard(self):
        """Test register payment wizard flow and invoice/payment posting."""
        entry = self.env['parking.entry'].create({
            'customer_type': 'public',
            'partner_id': self.partner.id,
            'vehicle_id': self.vehicle.id,
            'slot_type_id': self.slot_type.id,
            'slot_id': self.slot.id,
            'location_id': self.location.id,
            'parking_cost': 45.0,
        })
        entry.action_check_in()
        entry.action_check_out()

        wizard = self.env['register.payment.wizard'].with_context(
            active_id=entry.id,
        ).create({
            'partner_id': self.partner.id,
            'amount': 45.0,
            'ref': entry.name,
            'parking_duration': entry.duration or 1.0,
        })

        wizard.parking_payment()
        self.assertTrue(entry.paid_bool)
        self.assertEqual(entry.state, 'payment')

    def test_09_parking_ticket_report_render(self):
        """Test rendering the parking ticket report."""
        entry = self.env['parking.entry'].create({
            'customer_type': 'public',
            'partner_id': self.partner.id,
            'vehicle_id': self.vehicle.id,
            'slot_type_id': self.slot_type.id,
            'slot_id': self.slot.id,
            'location_id': self.location.id,
            'parking_cost': 20.0,
        })
        entry.action_check_in()
        report_action = self.env.ref('odoo_parking_management.report_parking_ticket')
        content, content_type = report_action._render_qweb_pdf(report_action.id, [entry.id])
        self.assertTrue(content)
        self.assertIn(content_type, ('pdf', 'html'))

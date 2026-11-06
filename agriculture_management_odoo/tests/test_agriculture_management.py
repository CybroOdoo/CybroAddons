# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
# pylint: disable=missing-module-docstring,unknown-option-value,too-few-public-methods,attribute-string-redundant,prefer-env-translation,duplicate-code,super-with-arguments,unused-argument,no-name-in-module,protected-access
"""Unit tests for Agriculture Management module."""
import os
from datetime import date, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.modules.module import get_module_path
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'agriculture_management_odoo')
class TestAgricultureManagement(TransactionCase):
    """Test suite covering agriculture management models, workflows, wizards,
    access control, and reporting.
    """

    @classmethod
    def setUpClass(cls):
        """Set up master test records."""
        super().setUpClass()
        cls.module_path = get_module_path('agriculture_management_odoo')
        cls.module = cls.env['ir.module.module'].search([
            ('name', '=', 'agriculture_management_odoo'),
        ], limit=1)

        # Master partner & farmer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Farmer John Doe',
            'email': 'farmer.john@gmail.com',
        })
        cls.farmer = cls.env['farmer.detail'].create({
            'farmer_id': cls.partner.id,
            'note': 'Experienced grain farmer',
        })

        # Seed and Location
        cls.seed = cls.env['seed.detail'].create({
            'name': 'Organic Wheat Seed',
            'quantity': 100,
            'unit': 'kg',
            'seed_type': 'certified',
        })
        cls.location = cls.env['location.detail'].create({
            'location_name': 'North Farm Sector A',
            'location_address': '123 Farm Road, Green Valley',
            'location_area': 100.0,
            'location_area_unit': 'acres',
            'location_type': 'plot',
        })

        # Animals & Vehicles
        cls.animal = cls.env['animal.detail'].create({
            'breed': 'Draft Bull Angus',
            'age': '3 Years',
            'state': 'available',
        })

        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'AgriPower',
        })
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'Tractor Pro 500',
            'brand_id': brand.id,
        })
        cls.fleet_veh = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'AGRI-7788',
            'registration_date': date.today(),
        })

        cls.vehicle = cls.env['vehicle.detail'].create({
            'vehicle_main_id': cls.fleet_veh.id,
            'vehicle_type': 'tractor',
        })

        # Pest
        cls.pest = cls.env['pest.detail'].create({
            'pest_name': 'Bio Pest Shield',
            'pest_cost': 25.0,
            'pest_quantity': 10,
            'pest_expiry_date': date.today() + timedelta(days=60),
        })

        cls.expired_pest = cls.env['pest.detail'].create({
            'pest_name': 'Old Chemical Spray',
            'pest_cost': 15.0,
            'pest_quantity': 5,
            'pest_expiry_date': date.today() - timedelta(days=10),
        })

    def test_01_module_installation_and_manifest(self):
        """Verify module is installed and manifest metadata is complete."""
        self.assertTrue(self.module, "Module must exist in ir.module.module.")
        self.assertEqual(
            self.module.state,
            'installed',
            "Module should be installed.",
        )
        self.assertEqual(self.module.license, 'LGPL-3')
        self.assertIn('Cybrosys', self.module.author)

    def test_02_agriculture_tags(self):
        """Verify agriculture.tag creation and default color generation."""
        tag = self.env['agriculture.tag'].create({
            'name': 'High Yield',
        })
        self.assertTrue(tag.id, "Tag must be created.")
        self.assertGreater(tag.color, 0, "Color index must be assigned.")

    def test_03_farmer_and_master_records(self):
        """Verify farmer onchange and seed/location/vehicle records."""
        self.farmer._onchange_farmer_id()
        self.assertEqual(self.farmer.farmer_id, self.partner)
        self.assertTrue(self.seed.id)
        self.assertTrue(self.location.id)
        self.assertTrue(self.vehicle.id)
        self.assertTrue(self.animal.id)
        self.assertIn('AGRI-7788', self.vehicle.name)

    def test_04_crop_request_workflow(self):
        """Verify crop.request creation and state progression."""
        crop_req = self.env['crop.request'].create({
            'farmer_id': self.farmer.id,
            'seed_id': self.seed.id,
            'location_id': self.location.id,
            'request_date': date.today(),
        })
        self.assertTrue(crop_req.ref, "Crop request reference should generate.")
        self.assertEqual(crop_req.state, 'draft')

        # Progression through all states
        crop_req.action_confirm()
        self.assertEqual(crop_req.state, 'confirm')
        crop_req.action_ploughing()
        self.assertEqual(crop_req.state, 'ploughing')
        crop_req.action_sowing()
        self.assertEqual(crop_req.state, 'sowing')
        crop_req.action_manuring()
        self.assertEqual(crop_req.state, 'manuring')
        crop_req.action_irrigation()
        self.assertEqual(crop_req.state, 'irrigation')
        crop_req.action_weeding()
        self.assertEqual(crop_req.state, 'weeding')
        crop_req.action_harvest()
        self.assertEqual(crop_req.state, 'harvest')
        crop_req.action_storage()
        self.assertEqual(crop_req.state, 'storage')
        crop_req.action_cancel()
        self.assertEqual(crop_req.state, 'cancel')
        crop_req.action_draft()
        self.assertEqual(crop_req.state, 'draft')

        expanded = crop_req._group_expand_states([], [])
        self.assertIn('draft', expanded)

    def test_05_pest_request_workflow(self):
        """Verify pest.request workflow including invoice generation."""
        crop_req = self.env['crop.request'].create({
            'farmer_id': self.farmer.id,
            'seed_id': self.seed.id,
            'location_id': self.location.id,
            'request_date': date.today(),
        })

        pest_req = self.env['pest.request'].create({
            'farmer_id': self.farmer.id,
            'crop_id': crop_req.id,
            'pest_id': self.pest.id,
            'pest_quantity': 4,
            'request_date': date.today(),
            'disease': 'Leaf rust',
        })
        self.assertTrue(pest_req.reference, "Pest request reference must exist.")
        self.assertEqual(pest_req.total_cost, 100.0)
        self.assertEqual(pest_req.state, 'draft')

        # Compute pest_ids
        pest_req._compute_pest_ids()
        self.assertIn(self.pest, pest_req.pest_ids)
        self.assertNotIn(self.expired_pest, pest_req.pest_ids)

        # Progress state
        pest_req.action_pending()
        self.assertEqual(pest_req.state, 'pending')
        pest_req.action_approved()
        self.assertEqual(pest_req.state, 'approve')

        # Create invoice
        inv_action = pest_req.action_create_invoice()
        self.assertTrue(pest_req.invoice_id)
        self.assertEqual(pest_req.state, 'invoiced')
        self.assertEqual(inv_action['res_model'], 'account.move')

        view_action = pest_req.action_view_invoice()
        self.assertEqual(view_action['res_model'], 'account.move')

        # Test rejection and draft
        pest_req.action_rejected()
        self.assertEqual(pest_req.state, 'rejected')
        pest_req.action_draft()
        self.assertEqual(pest_req.state, 'draft')

    def test_06_pest_request_expired_validation(self):
        """Verify validation errors when using expired pest."""
        crop_req = self.env['crop.request'].create({
            'farmer_id': self.farmer.id,
            'seed_id': self.seed.id,
            'location_id': self.location.id,
        })
        pest_req = self.env['pest.request'].create({
            'farmer_id': self.farmer.id,
            'crop_id': crop_req.id,
            'pest_id': self.expired_pest.id,
            'pest_quantity': 1,
            'disease': 'Leaf rust',
        })
        with self.assertRaises(ValidationError):
            pest_req.action_pending()
        with self.assertRaises(ValidationError):
            pest_req.action_approved()

    def test_07_animal_and_vehicle_rentals(self):
        """Verify rental date calculation, validations, and state progression."""
        start_d = date.today() - timedelta(days=2)
        end_d = date.today() + timedelta(days=3)

        # Animal Rental
        animal_rent = self.env['animal.rental'].create({
            'farmer_id': self.farmer.id,
            'animal_id': self.animal.id,
            'start_date': start_d,
            'end_date': end_d,
            'amount': 50.0,
        })
        self.assertEqual(animal_rent.no_of_days, 5)
        self.assertEqual(animal_rent.total_amount, 250.0)
        self.assertEqual(animal_rent.state, 'draft')

        animal_rent.action_confirm()
        self.assertEqual(animal_rent.state, 'confirm')
        animal_rent.action_return()
        self.assertEqual(animal_rent.state, 'return')
        animal_rent.action_cancel()
        self.assertEqual(animal_rent.state, 'cancel')
        animal_rent.action_draft()
        self.assertEqual(animal_rent.state, 'draft')

        # Vehicle Rental
        vehicle_rent = self.env['vehicle.rental'].create({
            'farmer_id': self.farmer.id,
            'vehicle_id': self.vehicle.id,
            'start_date': start_d,
            'end_date': end_d,
            'amount': 100.0,
        })
        self.assertEqual(vehicle_rent.no_of_days, 5)
        self.assertEqual(vehicle_rent.total_amount, 500.0)
        self.assertEqual(vehicle_rent.state, 'draft')

        vehicle_rent.action_confirm()
        self.assertEqual(vehicle_rent.state, 'confirm')
        vehicle_rent.action_return()
        self.assertEqual(vehicle_rent.state, 'return')
        vehicle_rent.action_cancel()
        self.assertEqual(vehicle_rent.state, 'cancel')
        vehicle_rent.action_draft()
        self.assertEqual(vehicle_rent.state, 'draft')

    def test_08_rental_invalid_date_validation(self):
        """Verify ValidationError when end_date < start_date."""
        start_d = date.today()
        end_d = date.today() - timedelta(days=2)

        with self.assertRaises(ValidationError):
            self.env['animal.rental'].create({
                'farmer_id': self.farmer.id,
                'animal_id': self.animal.id,
                'start_date': start_d,
                'end_date': end_d,
                'amount': 50.0,
            })

        with self.assertRaises(ValidationError):
            self.env['vehicle.rental'].create({
                'farmer_id': self.farmer.id,
                'vehicle_id': self.vehicle.id,
                'start_date': start_d,
                'end_date': end_d,
                'amount': 100.0,
            })

    def test_09_payment_wizards(self):
        """Verify animal and vehicle payment wizards."""
        animal_rent = self.env['animal.rental'].create({
            'farmer_id': self.farmer.id,
            'animal_id': self.animal.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=2),
            'amount': 50.0,
        })
        wizard_animal = self.env['animal.register.payment.wizard'].with_context(
            active_id=animal_rent.id,
        ).create({
            'farmer_id': self.farmer.id,
            'amount': 100.0,
            'ref': animal_rent.name,
        })
        wizard_animal.animal_rent_payment()
        self.assertTrue(animal_rent.animal_paid_bool)
        self.assertEqual(animal_rent.state, 'paid')

        vehicle_rent = self.env['vehicle.rental'].create({
            'farmer_id': self.farmer.id,
            'vehicle_id': self.vehicle.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=2),
            'amount': 100.0,
        })
        wizard_vehicle = self.env['vehicle.register.payment.wizard'].with_context(
            active_id=vehicle_rent.id,
        ).create({
            'farmer_id': self.farmer.id,
            'amount': 200.0,
            'ref': vehicle_rent.name,
        })
        wizard_vehicle.vehicle_rent_payment()
        self.assertTrue(vehicle_rent.vehicle_paid_bool)
        self.assertEqual(vehicle_rent.state, 'paid')

    def test_10_reports_wizards(self):
        """Verify crop and pest report wizards and action execution."""
        crop_wizard = self.env['crop.report'].create({
            'date_from': date.today() - timedelta(days=30),
            'date_to': date.today(),
        })
        crop_res = crop_wizard.action_pdf_report()
        self.assertTrue(crop_res)

        # Invalid future dates
        with self.assertRaises(UserError):
            self.env['crop.report'].create({
                'date_from': date.today() + timedelta(days=10),
            }).action_pdf_report()

        with self.assertRaises(UserError):
            self.env['pest.report'].create({
                'date_from': date.today() + timedelta(days=10),
            }).action_pdf_report()

    def test_11_damage_loss_machinery_and_inherited_fleet(self):
        """Verify damage loss, crop machinery, crop animal, and fleet vehicle."""
        crop_req = self.env['crop.request'].create({
            'farmer_id': self.farmer.id,
            'seed_id': self.seed.id,
            'location_id': self.location.id,
        })
        damage = self.env['damage.loss'].create({
            'name': 'Hailstorm Damage',
            'farmer_id': self.farmer.id,
            'crop_id': crop_req.id,
            'location_id': self.location.id,
            'damage_loss_type': 'damage',
            'damage_loss_date': date.today(),
        })
        self.assertTrue(damage.id)

        machinery = self.env['crop.machinery'].create({
            'vehicle_id': self.vehicle.id,
            'des_id': crop_req.id,
            'qty': 2,
        })
        self.assertTrue(machinery.id)

        crop_anim = self.env['crop.animal'].create({
            'animal_id': self.animal.id,
            'dec_id': crop_req.id,
            'qty': 2,
        })
        self.assertTrue(crop_anim.id)

    def test_12_security_access_rules(self):
        """Verify access controls for all agriculture models in ir.access."""
        group_admin = self.env.ref(
            'agriculture_management_odoo.group_agriculture_admin',
        )
        group_user = self.env.ref(
            'agriculture_management_odoo.group_agriculture_user',
        )
        self.assertTrue(group_admin)
        self.assertTrue(group_user)

        required_models = [
            'crop.request',
            'seed.detail',
            'animal.detail',
            'location.detail',
            'vehicle.detail',
            'farmer.detail',
            'pest.request',
            'pest.detail',
            'damage.loss',
            'crop.machinery',
            'crop.animal',
            'agriculture.tag',
            'vehicle.rental',
            'animal.rental',
            'fleet.vehicle',
        ]
        for model in required_models:
            access = self.env['ir.access'].search([
                ('model_id.model', '=', model),
                ('group_id', '=', group_admin.id),
            ])
            self.assertTrue(
                access,
                f"Access rule for model '{model}' and admin group must exist.",
            )

    def test_13_static_docs_and_assets(self):
        """Verify existence and validity of static resources and documents."""
        self.assertTrue(self.module_path)
        expected_files = [
            'README.rst',
            'doc/RELEASE_NOTES.md',
            'static/description/index.html',
            'static/description/icon.png',
            'static/description/banner.jpg',
        ]
        for rel_path in expected_files:
            full_path = os.path.join(self.module_path, rel_path)
            self.assertTrue(
                os.path.isfile(full_path),
                f"Required document '{rel_path}' must exist on disk.",
            )
            self.assertGreater(
                os.path.getsize(full_path),
                0,
                f"File '{rel_path}' must not be empty.",
            )

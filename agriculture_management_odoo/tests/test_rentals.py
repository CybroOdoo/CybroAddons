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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestRentals(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestRentals, cls).setUpClass()
        cls.company = cls.env.company

        # Create Partner for Farmer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Farmer',
            'email': 'farmer@example.com',
        })

        # Create Farmer Detail
        cls.farmer = cls.env['farmer.detail'].create({
            'farmer_id': cls.partner.id,
            'note': 'Test note for farmer',
        })

        # Create Brand, Model and Fleet Vehicle
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand',
        })
        cls.vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': cls.brand.id,
        })
        cls.fleet_vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.vehicle_model.id,
            'license_plate': 'TEST1234',
        })

        # Create Vehicle Detail
        cls.vehicle = cls.env['vehicle.detail'].create({
            'vehicle_main_id': cls.fleet_vehicle.id,
            'vehicle_type': 'tractor',
        })

        # Create Animal Detail
        cls.animal = cls.env['animal.detail'].create({
            'breed': 'Test Cow',
            'age': '5 years',
            'state': 'available',
        })

    def test_01_vehicle_rental(self):
        """Test vehicle rental creation, computation and states"""
        rental = self.env['vehicle.rental'].create({
            'farmer_id': self.farmer.id,
            'vehicle_id': self.vehicle.id,
            'start_date': '2026-05-01',
            'end_date': '2026-05-05',
            'amount': 100.0,
        })
        
        # Check initial state and computed values
        self.assertEqual(rental.state, 'draft')
        self.assertEqual(rental.no_of_days, 4)
        self.assertEqual(rental.total_amount, 400.0)

        # Confirm rental
        rental.action_confirm()
        self.assertEqual(rental.state, 'confirm')

        # Cancel rental
        rental.action_cancel()
        self.assertEqual(rental.state, 'cancel')
        
        # Return rental
        rental.start_date = '2020-05-01'  # to allow return
        rental.action_return()
        self.assertEqual(rental.state, 'return')

    def test_02_vehicle_rental_validation(self):
        """Test vehicle rental date validation"""
        with self.assertRaises(ValidationError):
            self.env['vehicle.rental'].create({
                'farmer_id': self.farmer.id,
                'vehicle_id': self.vehicle.id,
                'start_date': '2026-05-05',
                'end_date': '2026-05-01',
                'amount': 100.0,
            })

    def test_03_animal_rental(self):
        """Test animal rental creation, computation and states"""
        rental = self.env['animal.rental'].create({
            'farmer_id': self.farmer.id,
            'animal_id': self.animal.id,
            'start_date': '2026-05-01',
            'end_date': '2026-05-05',
            'amount': 50.0,
        })
        
        # Check initial state and computed values
        self.assertEqual(rental.state, 'draft')
        self.assertEqual(rental.no_of_days, 4)
        self.assertEqual(rental.total_amount, 200.0)

        # Confirm rental
        rental.action_confirm()
        self.assertEqual(rental.state, 'confirm')

        # Cancel rental
        rental.action_cancel()
        self.assertEqual(rental.state, 'cancel')
        
        # Return rental
        rental.start_date = '2020-05-01'  # to allow return
        rental.action_return()
        self.assertEqual(rental.state, 'return')

    def test_04_animal_rental_validation(self):
        """Test animal rental date validation"""
        with self.assertRaises(ValidationError):
            self.env['animal.rental'].create({
                'farmer_id': self.farmer.id,
                'animal_id': self.animal.id,
                'start_date': '2026-05-05',
                'end_date': '2026-05-01',
                'amount': 50.0,
            })

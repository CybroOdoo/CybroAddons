# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase
from odoo import fields


class TestDashboardFleetRental(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner1 = cls.env['res.partner'].create({
            'name': 'Customer One',
            'email': 'customer1@test.com',
            'phone': '123456789',
        })

        cls.partner2 = cls.env['res.partner'].create({
            'name': 'Customer Two',
            'email': 'customer2@test.com',
            'phone': '987654321',
        })

        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'BMW'
        })

        cls.vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'BMW X5',
            'vehicle_type': 'car',
            'brand_id': cls.brand.id,
        })

        cls.vehicle1 = cls.env['fleet.vehicle'].create({
            'name': 'Vehicle A',
            'rental_check_availability': True,
            'model_id': cls.vehicle_model.id,
        })

        cls.vehicle2 = cls.env['fleet.vehicle'].create({
            'name': 'Vehicle B',
            'rental_check_availability': False,
            'model_id': cls.vehicle_model.id,
        })

        cls.contract1 = cls.env['car.rental.contract'].create({
            'customer_id': cls.partner1.id,
            'vehicle_id': cls.vehicle1.id,
            'state': 'done',
            'rent_start_date': fields.Date.today(),
            'rent_end_date': fields.Date.today(),
            'cost_frequency': 'monthly',
            'cost': 100,
            'first_payment': 15
        })

        cls.contract2 = cls.env['car.rental.contract'].create({
            'customer_id': cls.partner1.id,
            'vehicle_id': cls.vehicle1.id,
            'state': 'running',
            'rent_start_date': fields.Date.today(),
            'rent_end_date': fields.Date.today(),
            'cost_frequency': 'yearly',
            'cost': 5000,
            'first_payment': 1500
        })

        cls.contract3 = cls.env['car.rental.contract'].create({
            'customer_id': cls.partner2.id,
            'vehicle_id': cls.vehicle2.id,
            'state': 'done',
            'rent_start_date': fields.Date.today(),
            'rent_end_date': fields.Date.today(),
            'cost_frequency': 'daily',
            'cost': 100,
            'first_payment': 5
        })

        cls.rental_model = cls.env['car.rental.contract']

    def test_vehicle_most_rented(self):
        result = self.rental_model.vehicle_most_rented(False, False)

        self.assertIn('name', result)
        self.assertIn('num', result)

        self.assertTrue(len(result['name']) > 0)
        self.assertEqual(result['name'][0], self.vehicle1.name)

    def test_cars_availability(self):
        result = self.rental_model.cars_availability()

        available_count = self.env['fleet.vehicle'].search_count([
            ('rental_check_availability', '=', True)
        ])

        self.assertIn('available_cars', result)
        self.assertIn('cars_running', result)
        self.assertEqual(result['available_cars'], available_count)
        self.assertEqual(result['cars_running'], 1)

    def test_car_details(self):
        result = self.rental_model.car_details()

        self.assertIn('running_details', result)
        self.assertIn('available_cars', result)

        self.assertEqual(len(result['running_details']), 1)

        running = result['running_details'][0]

        self.assertEqual(
            running['vehicle'],
            self.vehicle1.name
        )

        self.assertEqual(
            running['customer'],
            self.partner1.name
        )

    def test_top_customers(self):
        result = self.rental_model.top_customers()

        self.assertTrue(result)

        customer = result[0]

        self.assertEqual(
            customer['name'],
            self.partner1.name
        )

        self.assertEqual(
            customer['email'],
            self.partner1.email
        )

#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestFleetVehicle(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': cls.brand.id,
        })
        cls.vehicle1 = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'TEST-001',
            'vin_sn': 'VIN-001',
            'rental_check_availability': True,
            'color': '#FFFFFF',
            'fuel_type': 'gasoline',
        })

    def test_vehicle_creation(self):
        """ Test fleet vehicle fields and creation """
        self.assertEqual(self.vehicle1.license_plate, 'TEST-001')
        self.assertEqual(self.vehicle1.vin_sn, 'VIN-001')
        self.assertTrue(self.vehicle1.rental_check_availability)
        self.assertEqual(self.vehicle1.color, '#FFFFFF')
        self.assertEqual(self.vehicle1.fuel_type, 'gasoline')

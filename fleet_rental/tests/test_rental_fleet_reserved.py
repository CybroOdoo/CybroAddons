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
from datetime import date, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRentalFleetReserved(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'TEST-RES-001',
        })

    def test_rental_fleet_reserved_creation(self):
        """ Test rental fleet reserved creation """
        reserved = self.env['rental.fleet.reserved'].create({
            'customer_id': self.customer.id,
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=5),
            'reserved_obj_id': self.vehicle.id,
        })
        self.assertEqual(reserved.customer_id.name, 'Test Customer')
        self.assertEqual(reserved.reserved_obj_id.license_plate, 'TEST-RES-001')

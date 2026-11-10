# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase


class DriveXCommon(TransactionCase):
    """Common records for the DriveX tests."""

    @classmethod
    def setUpClass(cls):
        """Create a vehicle and rental locations."""
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'DriveX Test Brand',
        })
        cls.vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'DriveX Test Model',
            'brand_id': brand.id,
        })
        cls.vehicle = cls._create_vehicle()
        cls.location = cls.env['fleet.rental.location'].create({
            'name': 'DriveX Test Location',
        })

    @classmethod
    def _create_vehicle(cls, **values):
        """Create a vehicle of the test model."""
        return cls.env['fleet.vehicle'].create({
            'model_id': cls.vehicle_model.id,
            'daily_rate': 100.0,
            **values,
        })

    def _create_order(self, pickup, return_date, **values):
        """Create a rental order for the test vehicle."""
        return self.env['fleet.rental.order'].create({
            'vehicle_id': self.vehicle.id,
            'pickup_datetime': pickup,
            'return_datetime': return_date,
            'pickup_location_id': self.location.id,
            'return_location_id': self.location.id,
            'driver_name': 'Test Driver',
            'driver_email': 'driver@example.com',
            'driver_phone': '+910000000000',
            **values,
        })

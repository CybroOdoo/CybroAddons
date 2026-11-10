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
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import DriveXCommon


@tagged('post_install', '-at_install')
class TestFleetVehicle(DriveXCommon):
    """Tests for the DriveX fields of the fleet.vehicle model."""

    def test_default_values(self):
        """New vehicles are on the website but not on the homepage."""
        self.assertTrue(self.vehicle.is_available_on_website)
        self.assertFalse(self.vehicle.publish_on_homepage)
        self.assertEqual(self.vehicle.currency_id,
                         self.vehicle.company_id.currency_id)

    def test_check_homepage_vehicles(self):
        """At most 3 vehicles can be shown on the homepage."""
        self.env['fleet.vehicle'].search(
            [('publish_on_homepage', '=', True)]).publish_on_homepage = False
        for _index in range(3):
            self._create_vehicle(publish_on_homepage=True)
        with self.assertRaises(ValidationError):
            self.vehicle.publish_on_homepage = True

    def test_vehicle_images(self):
        """Gallery images are deleted with their vehicle."""
        vehicle = self._create_vehicle()
        image = self.env['fleet.vehicle.image'].create({
            'vehicle_id': vehicle.id,
            'image': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4'
                     '2mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
        })
        vehicle.unlink()
        self.assertFalse(image.exists())

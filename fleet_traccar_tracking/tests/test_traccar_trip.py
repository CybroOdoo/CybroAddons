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
from odoo.tests.common import TransactionCase
from datetime import datetime, timedelta

class TestTraccarTrip(TransactionCase):

    def setUp(self):
        super(TestTraccarTrip, self).setUp()
        self.vehicle = self.env['fleet.vehicle'].create({'name': 'V1'})

    def test_compute_duration(self):
        """Verify trip duration calculation in minutes."""
        start = datetime(2026, 1, 1, 10, 0, 0)
        end = datetime(2026, 1, 1, 10, 45, 0)
        trip = self.env['fleet.traccar.trip'].create({
            'vehicle_id': self.vehicle.id,
            'start_time': start,
            'end_time': end,
        })
        trip._compute_duration()
        self.assertEqual(trip.duration, 45.0)

    def test_compute_display_name(self):
        """Verify display name generation for trips."""
        start = datetime(2026, 1, 1, 10, 0, 0)
        trip = self.env['fleet.traccar.trip'].create({
            'vehicle_id': self.vehicle.id,
            'start_time': start,
        })
        trip._compute_display_name()
        self.assertIn('V1', trip.display_name)
        self.assertIn('2026-01-01', trip.display_name)

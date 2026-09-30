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
from datetime import datetime

class TestTraccarPosition(TransactionCase):

    def test_create_position(self):
        """Verify position record creation and sorting."""
        vehicle = self.env['fleet.vehicle'].create({'name': 'V1'})
        pos = self.env['fleet.traccar.position'].create({
            'vehicle_id': vehicle.id,
            'latitude': 48.8566,
            'longitude': 2.3522,
            'speed': 50.0,
            'fix_time': datetime.now(),
            'attributes': {'protocol': 'osmand'}
        })
        self.assertEqual(pos.latitude, 48.8566)
        self.assertEqual(pos.attributes.get('protocol'), 'osmand')

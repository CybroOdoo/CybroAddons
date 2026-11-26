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

class TestTraccarEvent(TransactionCase):

    def test_create_event(self):
        """Verify event creation and field mapping."""
        brand = self.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'})
        model = self.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': brand.id,
        })
        vehicle = self.env['fleet.vehicle'].create({
            'model_id': model.id,
            'name': 'V1',
        })
        event = self.env['fleet.traccar.event'].create({
            'vehicle_id': vehicle.id,
            'event_type': 'deviceOverspeed',
            'event_time': datetime.now(),
            'traccar_event_id': 55,
            'attributes': {'speed': 110}
        })
        self.assertEqual(event.event_type, 'deviceOverspeed')
        self.assertEqual(event.attributes.get('speed'), 110)

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

class TestTraccarDevice(TransactionCase):

    def setUp(self):
        super(TestTraccarDevice, self).setUp()
        self.device = self.env['fleet.traccar.device'].create({
            'name': 'Test Device',
            'traccar_id': 123,
            'unique_id': 'unique-123',
        })

    def test_compute_position_count(self):
        """Test the position count computation for a device."""
        self.env['fleet.traccar.position'].create({
            'device_id': self.device.id,
            'fix_time': '2026-06-06 12:00:00'
        })
        self.device._compute_position_count()
        self.assertEqual(self.device.position_count, 1)

    def test_action_view_positions(self):
        """Test the window action to view device positions."""
        action = self.device.action_view_positions()
        self.assertEqual(action.get('res_model'), 'fleet.traccar.position')
        self.assertEqual(action.get('domain'), [('device_id', '=', self.device.id)])

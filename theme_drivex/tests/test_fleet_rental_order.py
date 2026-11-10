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
class TestFleetRentalOrder(DriveXCommon):
    """Tests for the fleet.rental.order model."""

    def test_create_assigns_sequence(self):
        """A new booking gets its reference from the sequence."""
        order = self._create_order('2030-01-01 10:00:00',
                                   '2030-01-03 10:00:00')
        self.assertNotEqual(order.name, 'New')
        self.assertTrue(order.name.startswith('BKG-'))

    def test_create_keeps_given_name(self):
        """A booking reference given at creation is kept."""
        order = self._create_order('2030-01-01 10:00:00',
                                   '2030-01-03 10:00:00', name='BKG-CUSTOM')
        self.assertEqual(order.name, 'BKG-CUSTOM')

    def test_compute_amount_total(self):
        """The total is the sum of base, insurance and add-on amounts."""
        order = self._create_order('2030-01-01 10:00:00',
                                   '2030-01-03 10:00:00',
                                   amount_base=200.0, amount_insurance=30.0,
                                   amount_addons=20.0)
        self.assertEqual(order.amount_total, 250.0)
        order.amount_addons = 0.0
        self.assertEqual(order.amount_total, 230.0)

    def test_state_actions(self):
        """The action buttons move the booking through its states."""
        order = self._create_order('2030-01-01 10:00:00',
                                   '2030-01-03 10:00:00')
        self.assertEqual(order.state, 'draft')
        order.action_confirm()
        self.assertEqual(order.state, 'confirmed')
        order.action_pickup()
        self.assertEqual(order.state, 'picked_up')
        order.action_return()
        self.assertEqual(order.state, 'returned')
        order.action_cancel()
        self.assertEqual(order.state, 'cancelled')

    def test_check_overlap_confirmed(self):
        """Two confirmed bookings of a vehicle cannot overlap."""
        self._create_order('2030-02-01 10:00:00', '2030-02-05 10:00:00',
                           state='confirmed')
        with self.assertRaises(ValidationError):
            self._create_order('2030-02-04 10:00:00', '2030-02-08 10:00:00',
                               state='confirmed')

    def test_check_overlap_on_confirm(self):
        """Confirming a draft booking that overlaps is refused."""
        self._create_order('2030-03-01 10:00:00', '2030-03-05 10:00:00',
                           state='confirmed')
        draft = self._create_order('2030-03-02 10:00:00',
                                   '2030-03-03 10:00:00')
        with self.assertRaises(ValidationError):
            draft.action_confirm()

    def test_check_overlap_allowed(self):
        """Back-to-back and cancelled bookings do not conflict."""
        first = self._create_order('2030-04-01 10:00:00',
                                   '2030-04-05 10:00:00', state='confirmed')
        self._create_order('2030-04-05 10:00:00', '2030-04-08 10:00:00',
                           state='confirmed')
        first.action_cancel()
        order = self._create_order('2030-04-02 10:00:00',
                                   '2030-04-04 10:00:00', state='confirmed')
        self.assertEqual(order.state, 'confirmed')

    def test_check_overlap_other_vehicle(self):
        """The same dates can be booked for another vehicle."""
        self._create_order('2030-05-01 10:00:00', '2030-05-05 10:00:00',
                           state='confirmed')
        other_vehicle = self._create_vehicle()
        order = self._create_order('2030-05-01 10:00:00',
                                   '2030-05-05 10:00:00', state='confirmed',
                                   vehicle_id=other_vehicle.id)
        self.assertEqual(order.vehicle_id, other_vehicle)

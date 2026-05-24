# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Manasa T P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSlotTime(TransactionCase):
    """Test cases for the slot.time model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SlotTime = cls.env['slot.time']

    def test_create_slot_time_minimal(self):
        """Test creating a slot.time record with only required fields."""
        slot = self.SlotTime.create({
            'name': 'Morning Slot',
            'time_from': '8',
            'time_to': '12',
        })
        self.assertEqual(slot.name, 'Morning Slot')
        self.assertEqual(slot.time_from, '8')
        self.assertEqual(slot.time_to, '12')
        self.assertFalse(slot.slot_type,
                         "slot_type should be False/unset when not provided")

    def test_create_slot_time_home(self):
        """Test creating a slot.time record with Home Hours slot type."""
        slot = self.SlotTime.create({
            'name': 'Home Evening',
            'slot_type': 'home',
            'time_from': '18',
            'time_to': '21',
        })
        self.assertEqual(slot.slot_type, 'home')

    def test_create_slot_time_office(self):
        """Test creating a slot.time record with Office Hours slot type."""
        slot = self.SlotTime.create({
            'name': 'Office Morning',
            'slot_type': 'office',
            'time_from': '9',
            'time_to': '17',
        })
        self.assertEqual(slot.slot_type, 'office')

    def test_name_is_required(self):
        """Test that name field is required."""
        with self.assertRaises(Exception):
            self.SlotTime.create({
                'time_from': '8',
                'time_to': '12',
            })

    def test_time_from_is_required(self):
        """Test that time_from field is required."""
        with self.assertRaises(Exception):
            self.SlotTime.create({
                'name': 'Slot Without From',
                'time_to': '12',
            })

    def test_time_to_is_required(self):
        """Test that time_to field is required."""
        with self.assertRaises(Exception):
            self.SlotTime.create({
                'name': 'Slot Without To',
                'time_from': '8',
            })

    def test_all_valid_time_from_values(self):
        """Test creating slots with boundary time_from values (0 and 23)."""
        slot_midnight = self.SlotTime.create({
            'name': 'Midnight Start',
            'time_from': '0',
            'time_to': '1',
        })
        self.assertEqual(slot_midnight.time_from, '0')

        slot_late = self.SlotTime.create({
            'name': 'Late Night Start',
            'time_from': '23',
            'time_to': '23',
        })
        self.assertEqual(slot_late.time_from, '23')

    def test_all_valid_time_to_values(self):
        """Test creating slots with boundary time_to values (0 and 23)."""
        slot = self.SlotTime.create({
            'name': 'Midnight End',
            'time_from': '0',
            'time_to': '0',
        })
        self.assertEqual(slot.time_to, '0')

        slot_late = self.SlotTime.create({
            'name': 'Last Hour End',
            'time_from': '22',
            'time_to': '23',
        })
        self.assertEqual(slot_late.time_to, '23')

    def test_multiple_slots_can_be_created(self):
        """Test that multiple distinct slot.time records can coexist."""
        slot1 = self.SlotTime.create({
            'name': 'Slot A',
            'time_from': '8',
            'time_to': '10',
        })
        slot2 = self.SlotTime.create({
            'name': 'Slot B',
            'time_from': '10',
            'time_to': '12',
        })
        self.assertNotEqual(slot1.id, slot2.id)

    def test_update_slot_name(self):
        """Test updating the name of an existing slot.time record."""
        slot = self.SlotTime.create({
            'name': 'Old Name',
            'time_from': '6',
            'time_to': '8',
        })
        slot.write({'name': 'New Name'})
        self.assertEqual(slot.name, 'New Name')

    def test_update_slot_type(self):
        """Test updating slot_type after creation."""
        slot = self.SlotTime.create({
            'name': 'Flexible Slot',
            'time_from': '10',
            'time_to': '14',
        })
        self.assertFalse(slot.slot_type)
        slot.write({'slot_type': 'office'})
        self.assertEqual(slot.slot_type, 'office')

    def test_description(self):
        """Test that the model description is correct."""
        self.assertEqual(
            self.env['slot.time']._description, 'Delivery time')

    def test_model_name(self):
        """Test that the model technical name is correct."""
        self.assertEqual(
            self.env['slot.time']._name, 'slot.time')

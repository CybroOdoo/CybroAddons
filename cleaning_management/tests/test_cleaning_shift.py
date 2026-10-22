# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB(odoo@cybrosys.com)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCleaningShift(TransactionCase):
    """Test cases for cleaning.shift model."""

    def setUp(self):
        super().setUp()
        self.CleaningShift = self.env['cleaning.shift']
        self.shift = self.CleaningShift.create({
            'shift_type': 'Morning Shift',
            'shift_time_from': 8.0,
            'shift_time_to': 16.0,
        })

    def test_create_shift(self):
        """Test creating a cleaning shift."""
        self.assertEqual(self.shift.shift_type, 'Morning Shift')
        self.assertEqual(self.shift.shift_time_from, 8.0)
        self.assertEqual(self.shift.shift_time_to, 16.0)

    def test_shift_rec_name(self):
        """Test that rec_name returns shift_type."""
        self.assertEqual(self.shift.display_name, 'Morning Shift')

    def test_shift_required_fields(self):
        """Test required fields on shift creation."""
        with self.assertRaises(Exception):
            self.CleaningShift.create({'shift_type': 'Evening'})
        with self.assertRaises(Exception):
            self.CleaningShift.create({
                'shift_time_from': 16.0,
                'shift_time_to': 23.0,
            })
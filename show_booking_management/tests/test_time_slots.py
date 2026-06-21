# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestTimeSlots(TransactionCase):
    """Test cases for time.slots model functions."""

    # -------------------------------------------------------------------------
    # create
    # -------------------------------------------------------------------------
    def test_create_valid_time(self):
        """Test create successfully converts 24h time to 12h name."""
        slot = self.env['time.slots'].create({'movie_time': '14:30'})
        self.assertEqual(slot.name, '02:30 PM')
        # Colons replaced with dots for movie_time
        self.assertEqual(slot.movie_time, '14.30')

    def test_create_morning_time(self):
        """Test create correctly formats AM time."""
        slot = self.env['time.slots'].create({'movie_time': '09:00'})
        self.assertEqual(slot.name, '09:00 AM')

    def test_create_no_movie_time(self):
        """Test create raises ValidationError when movie_time is missing."""
        with self.assertRaises(ValidationError):
            self.env['time.slots'].create({'movie_time': ''})

    def test_create_invalid_time_format(self):
        """Test create raises ValidationError for bad time format."""
        with self.assertRaises(ValidationError):
            self.env['time.slots'].create({'movie_time': '25:99'})

    # -------------------------------------------------------------------------
    # write
    # -------------------------------------------------------------------------
    def test_write_updates_name_and_movie_time(self):
        """Test write updates the name and formats movie_time correctly."""
        slot = self.env['time.slots'].create({'movie_time': '10:00'})
        slot.write({'movie_time': '20:45'})
        self.assertEqual(slot.name, '08:45 PM')
        self.assertEqual(slot.movie_time, '20.45')

    def test_write_invalid_time_format(self):
        """Test write raises ValidationError for bad time format."""
        slot = self.env['time.slots'].create({'movie_time': '10:00'})
        with self.assertRaises(ValidationError):
            slot.write({'movie_time': 'abc'})

    def test_write_without_movie_time_does_not_update_name(self):
        """Test write without movie_time does not change the slot name."""
        slot = self.env['time.slots'].create({'movie_time': '11:00'})
        original_name = slot.name
        slot.write({'movie_time': False})
        self.assertEqual(slot.name, original_name)

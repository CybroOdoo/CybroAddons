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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError



class TestTimeSlots(TransactionCase):
    """Test cases for time.slots model"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TimeSlots = cls.env['time.slots']

    # ── create ────────────────────────────────────────────────────────────────

    def test_create_am_slot_formats_correctly(self):
        """AM time is formatted to 12-hour name and dot-separated movie_time"""
        slot = self.TimeSlots.create({'movie_time': '09:00'})
        self.assertEqual(slot.name, '09:00 AM')
        self.assertEqual(slot.movie_time, '09.00')

    def test_create_pm_slot_formats_correctly(self):
        """PM time is formatted to 12-hour name with PM suffix"""
        slot = self.TimeSlots.create({'movie_time': '14:30'})
        self.assertEqual(slot.name, '02:30 PM')
        self.assertEqual(slot.movie_time, '14.30')

    def test_create_midnight_slot(self):
        """Midnight (00:00) formats to 12:00 AM"""
        slot = self.TimeSlots.create({'movie_time': '00:00'})
        self.assertEqual(slot.name, '12:00 AM')
        self.assertEqual(slot.movie_time, '00.00')

    def test_create_noon_slot(self):
        """Noon (12:00) formats to 12:00 PM"""
        slot = self.TimeSlots.create({'movie_time': '12:00'})
        self.assertEqual(slot.name, '12:00 PM')
        self.assertEqual(slot.movie_time, '12.00')

    def test_create_evening_slot(self):
        """Evening time formats correctly"""
        slot = self.TimeSlots.create({'movie_time': '18:45'})
        self.assertEqual(slot.name, '06:45 PM')
        self.assertEqual(slot.movie_time, '18.45')

    def test_create_without_movie_time_raises(self):
        """Creating without movie_time raises ValidationError"""
        with self.assertRaises(Exception):
            self.TimeSlots.create({'movie_time': ''})

    # ── write ─────────────────────────────────────────────────────────────────

    def test_write_updates_name_and_movie_time(self):
        """write() with new movie_time updates both name and movie_time"""
        slot = self.TimeSlots.create({'movie_time': '09:00'})
        self.assertEqual(slot.name, '09:00 AM')
        slot.write({'movie_time': '18:45'})
        self.assertEqual(slot.name, '06:45 PM')
        self.assertEqual(slot.movie_time, '18.45')

    def test_write_am_to_pm(self):
        """write() correctly converts AM slot to PM"""
        slot = self.TimeSlots.create({'movie_time': '08:00'})
        slot.write({'movie_time': '20:00'})
        self.assertEqual(slot.name, '08:00 PM')
        self.assertEqual(slot.movie_time, '20.00')

    def test_write_pm_to_am(self):
        """write() correctly converts PM slot to AM"""
        slot = self.TimeSlots.create({'movie_time': '20:00'})
        slot.write({'movie_time': '06:30'})
        self.assertEqual(slot.name, '06:30 AM')
        self.assertEqual(slot.movie_time, '06.30')

    # ── unique name constraint ────────────────────────────────────────────────

    def test_unique_name_constraint(self):
        """Creating two time slots with the same time raises an integrity error"""
        from odoo.tools import mute_logger
        self.TimeSlots.create({'movie_time': '11:00'})
        with self.assertRaises(Exception), mute_logger('odoo.sql_db'):
            # Unique constraint on name prevents duplicate slot at same time
            self.TimeSlots.create({'movie_time': '11:00'})

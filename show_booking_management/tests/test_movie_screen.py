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



class TestMovieScreen(TransactionCase):
    """Test cases for movie.screen model"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.MovieScreen = cls.env['movie.screen']
        cls.screen = cls.MovieScreen.create({
            'name': 'Main Screen',
            'total_rows': 10,
            'no_of_seat_row': 15,
        })

    # ── Creation ──────────────────────────────────────────────────────────────

    def test_screen_creation(self):
        """Screen is created with correct attributes"""
        self.assertEqual(self.screen.name, 'Main Screen')
        self.assertEqual(self.screen.total_rows, 10)
        self.assertEqual(self.screen.no_of_seat_row, 15)

    # ── Computed total_seat_count ─────────────────────────────────────────────

    def test_total_seat_count_computed_correctly(self):
        """total_seat_count = total_rows * no_of_seat_row"""
        self.assertEqual(self.screen.total_seat_count, 150)

    def test_total_seat_count_updates_on_row_change(self):
        """total_seat_count recalculates when total_rows changes"""
        self.screen.write({'total_rows': 5})
        self.assertEqual(self.screen.total_seat_count, 75)
        self.screen.write({'total_rows': 10})  # restore

    def test_total_seat_count_updates_on_seats_per_row_change(self):
        """total_seat_count recalculates when no_of_seat_row changes"""
        self.screen.write({'no_of_seat_row': 20})
        self.assertEqual(self.screen.total_seat_count, 200)
        self.screen.write({'no_of_seat_row': 15})  # restore

    def test_total_seat_count_zero_when_rows_zero(self):
        """total_seat_count is 0 when total_rows is 0"""
        screen = self.MovieScreen.create({
            'name': 'Zero Row Screen',
            'total_rows': 0,
            'no_of_seat_row': 10,
        })
        self.assertEqual(screen.total_seat_count, 0)

    def test_total_seat_count_zero_when_seats_per_row_zero(self):
        """total_seat_count is 0 when no_of_seat_row is 0"""
        screen = self.MovieScreen.create({
            'name': 'Zero Seat Screen',
            'total_rows': 10,
            'no_of_seat_row': 0,
        })
        self.assertEqual(screen.total_seat_count, 0)

    def test_multiple_screens_independent(self):
        """Multiple screens maintain independent seat counts"""
        screen_a = self.MovieScreen.create({
            'name': 'Screen A', 'total_rows': 8, 'no_of_seat_row': 8})
        screen_b = self.MovieScreen.create({
            'name': 'Screen B', 'total_rows': 12, 'no_of_seat_row': 10})
        self.assertEqual(screen_a.total_seat_count, 64)
        self.assertEqual(screen_b.total_seat_count, 120)

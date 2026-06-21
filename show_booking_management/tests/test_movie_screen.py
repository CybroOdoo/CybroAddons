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


@tagged('post_install', '-at_install')
class TestMovieScreen(TransactionCase):
    """Test cases for movie.screen model functions."""

    def setUp(self):
        super(TestMovieScreen, self).setUp()
        self.screen = self.env['movie.screen'].create({
            'name': 'Screen Test',
            'total_rows': 8,
            'no_of_seat_row': 12,
        })

    # -------------------------------------------------------------------------
    # _compute_total_seat_count
    # -------------------------------------------------------------------------
    def test_compute_total_seat_count_valid(self):
        """Test total seat count is correctly calculated as rows * seats per row."""
        self.screen._compute_total_seat_count()
        self.assertEqual(self.screen.total_seat_count, 96)

    def test_compute_total_seat_count_zero_rows(self):
        """Test total seat count is 0 when total_rows is 0."""
        screen = self.env['movie.screen'].create({
            'name': 'Empty Screen',
            'total_rows': 0,
            'no_of_seat_row': 12,
        })
        screen._compute_total_seat_count()
        self.assertEqual(screen.total_seat_count, 0)

    def test_compute_total_seat_count_zero_seats_per_row(self):
        """Test total seat count is 0 when no_of_seat_row is 0."""
        screen = self.env['movie.screen'].create({
            'name': 'Empty Screen 2',
            'total_rows': 8,
            'no_of_seat_row': 0,
        })
        screen._compute_total_seat_count()
        self.assertEqual(screen.total_seat_count, 0)

    def test_compute_total_seat_count_updated_on_write(self):
        """Test total_seat_count recomputes when rows/seats_per_row is updated."""
        self.screen.write({'total_rows': 5, 'no_of_seat_row': 20})
        self.screen._compute_total_seat_count()
        self.assertEqual(self.screen.total_seat_count, 100)

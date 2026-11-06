# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
################################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMoveLine(TransactionCase):
    """Tests for account.move.line dimension fields."""

    def test_compute_area_m2_valid(self):
        """Test area is computed correctly given length and width."""
        line = self.env['account.move.line'].new({
            'length_mm': 2000.0,
            'width_mm': 1000.0,
        })
        line._compute_area_m2()
        self.assertEqual(line.area_m2, 2.0)

    def test_compute_area_m2_zero(self):
        """Test area is 0 when length or width is 0."""
        line = self.env['account.move.line'].new({
            'length_mm': 2000.0,
            'width_mm': 0.0,
        })
        line._compute_area_m2()
        self.assertEqual(line.area_m2, 0.0)

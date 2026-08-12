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
class TestPurchaseOrderLine(TransactionCase):
    """Tests for purchase.order.line dimension fields and onchange logic."""

    def test_compute_area_valid(self):
        """Test _compute_area correctly calculates area_m2 from length and width."""
        line = self.env['purchase.order.line'].new({
            'length_mm': 2000.0,
            'width_mm': 1000.0,
        })
        line._compute_area()
        self.assertEqual(line.area_m2, 2.0)

    def test_compute_area_zero(self):
        """Test _compute_area sets area_m2 to 0 when length or width is missing."""
        line = self.env['purchase.order.line'].new({
            'length_mm': 2000.0,
            'width_mm': 0.0,
        })
        line._compute_area()
        self.assertEqual(line.area_m2, 0.0)

    def test_onchange_area_price_qty(self):
        """Test _onchange_area_price_qty recalculates unit price dynamically."""
        line = self.env['purchase.order.line'].new({
            'area_m2': 2.0,
            'price_per_m2': 50.0,
        })
        line._onchange_area_price_qty()
        self.assertEqual(line.price_unit, 100.0)

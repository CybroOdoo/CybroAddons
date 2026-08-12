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
class TestSaleOrderLine(TransactionCase):
    """Tests for sale.order.line dimension fields and onchange logic."""

    def setUp(self):
        super(TestSaleOrderLine, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
        })
        self.so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.so_line = self.env['sale.order.line'].create({
            'order_id': self.so.id,
            'product_id': self.product.id,
            'length_mm': 2000.0,
            'width_mm': 1000.0,
            'price_per_m2': 50.0,
        })

    def test_compute_area_valid(self):
        """Test _compute_area correctly calculates area_m2 from length and width."""
        self.assertEqual(self.so_line.area_m2, 2.0)

    def test_compute_area_zero(self):
        """Test _compute_area sets area_m2 to 0 when length or width is missing."""
        self.so_line.width_mm = 0.0
        self.assertEqual(self.so_line.area_m2, 0.0)

    def test_onchange_area_price_qty(self):
        """Test _onchange_area_price_qty recalculates unit price dynamically."""
        self.so_line._onchange_area_price_qty()
        self.assertEqual(self.so_line.price_unit, 100.0)

    def test_prepare_invoice_line(self):
        """Test _prepare_invoice_line includes product dimension fields."""
        vals = self.so_line._prepare_invoice_line()
        self.assertIn('length_mm', vals)
        self.assertIn('width_mm', vals)
        self.assertIn('area_m2', vals)
        self.assertIn('price_per_m2', vals)
        self.assertEqual(vals['length_mm'], 2000.0)
        self.assertEqual(vals['width_mm'], 1000.0)
        self.assertEqual(vals['area_m2'], 2.0)
        self.assertEqual(vals['price_per_m2'], 50.0)

# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase



class TestBookOrderLine(TransactionCase):
    """Test cases for the book.order.line model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Line Test Customer',
        })
        cls.order = cls.env['book.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Line Test Product',
            'list_price': 200.0,
        })
        cls.tax_10 = cls.env['account.tax'].create({
            'name': 'Tax 10%',
            'amount_type': 'percent',
            'amount': 10.0,
        })

    def test_compute_amount_line_all_no_tax(self):
        """Test subtotal calculation without taxes."""
        line = self.env['book.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'qty': 2.0,
            'price_unit': 200.0,
        })
        self.assertAlmostEqual(line.price_subtotal, 400.0)
        self.assertAlmostEqual(line.price_subtotal_incl, 400.0)

    def test_compute_amount_line_all_with_tax(self):
        """Test subtotal calculation with taxes."""
        line = self.env['book.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'qty': 1.0,
            'price_unit': 100.0,
            'tax_ids': [(4, self.tax_10.id)],
        })
        self.assertAlmostEqual(line.price_subtotal, 100.0)
        self.assertAlmostEqual(line.price_subtotal_incl, 110.0)

    def test_compute_amount_line_all_with_discount(self):
        """Test subtotal calculation with a discount."""
        line = self.env['book.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'qty': 2.0,
            'price_unit': 100.0,
            'discount': 20.0, # 20% discount
            'tax_ids': [(4, self.tax_10.id)],
        })
        # Price: 100, Qty: 2 = 200
        # Discount 20% = 40. Subtotal before tax = 160.
        # Tax 10% of 160 = 16. Total = 176.
        self.assertAlmostEqual(line.price_subtotal, 160.0)
        self.assertAlmostEqual(line.price_subtotal_incl, 176.0)

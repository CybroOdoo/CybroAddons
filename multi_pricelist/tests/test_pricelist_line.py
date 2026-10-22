# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestPricelistLine(TransactionCase):
    """Test cases for pricelist.line model"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'standard_price': 60.0,
        })

        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Pricelist',
        })

        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
        })

        cls.order_line = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order.id,
            'product_id': cls.product.id,
            'product_uom_qty': 1,
            'price_unit': 100,
            'name': cls.product.name,
        })

        cls.wizard = cls.env['pricelist.product'].create({
            'order_line_id': cls.order_line.id,
        })

    def test_compute_margin_with_cost(self):
        """Test margin computation when unit_cost is non-zero.
        Formula: ((unit_price - unit_cost) / unit_cost) * 100"""

        line = self.env['pricelist.line'].create({
            'wizard_id': self.wizard.id,
            'pricelist_id': self.pricelist.id,
            'product_id': self.product.id,
            'unit_price': 100,
            'unit_cost': 50,
            'uom_id': self.product.uom_id.id,
        })

        self.assertAlmostEqual(line.margin, 100.0)

    def test_compute_margin_zero_cost(self):
        """Test margin defaults to 100 when unit_cost is zero"""

        line = self.env['pricelist.line'].create({
            'wizard_id': self.wizard.id,
            'pricelist_id': self.pricelist.id,
            'product_id': self.product.id,
            'unit_price': 100,
            'unit_cost': 0,
            'uom_id': self.product.uom_id.id,
        })

        self.assertEqual(line.margin, 100.0)

    def test_compute_margin_negative(self):
        """Test margin is negative when price is below cost"""

        line = self.env['pricelist.line'].create({
            'wizard_id': self.wizard.id,
            'pricelist_id': self.pricelist.id,
            'product_id': self.product.id,
            'unit_price': 40,
            'unit_cost': 50,
            'uom_id': self.product.uom_id.id,
        })

        self.assertAlmostEqual(line.margin, -20.0)

    def test_apply_pricelist_updates_order_line(self):
        """Test that apply_pricelist sets the pricelist and price on order line"""

        line = self.env['pricelist.line'].create({
            'wizard_id': self.wizard.id,
            'pricelist_id': self.pricelist.id,
            'product_id': self.product.id,
            'unit_price': 90,
            'unit_cost': 50,
            'uom_id': self.product.uom_id.id,
        })

        line.apply_pricelist()

        self.assertEqual(
            self.order_line.applied_pricelist_id,
            self.pricelist,
            "applied_pricelist_id should be updated to the selected pricelist",
        )

        self.assertAlmostEqual(
            self.order_line.price_unit,
            90,
            msg="price_unit should be updated to the pricelist unit price",
        )

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'advance_product_dimension')
class TestSaleOrder(TransactionCase):
    """
    Test suite for models/sale_order.py (SaleOrder model).

    Covers:
        - _compute_tax_totals
        - _compute_amounts
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})

        # Tax
        cls.tax_10 = cls.env['account.tax'].create({
            'name': 'Tax 10%',
            'amount_type': 'percent',
            'amount': 10.0,
        })

        # Dimension-based product
        cls.product_dim = cls.env['product.product'].create({
            'name': 'Dim Product',
            'price_calculation_based_on': 'based_on_dimension',
            'uom_prompt_id': cls.uom_unit.id,
            'list_price': 50.0,
            'taxes_id': [(6, 0, cls.tax_10.ids)],
            'type': 'consu',
        })

        # Quantity-based product
        cls.product_qty = cls.env['product.product'].create({
            'name': 'Qty Product',
            'price_calculation_based_on': 'based_on_quantity',
            'list_price': 100.0,
            'taxes_id': [(6, 0, cls.tax_10.ids)],
            'type': 'consu',
        })

    def test_compute_amounts_and_tax_totals_dimension_based(self):
        """Test amounts and tax totals for a dimension-based product."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_dim.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 50.0,
                    'length': 2.0,
                    'width': 3.0,
                    'height': 4.0, # dim_qty = 24
                    'tax_id': [(6, 0, self.tax_10.ids)],
                })
            ]
        })
        # dim_qty = 24, price = 50 -> base_price = 1200
        # qty = 2 -> subtotal = 2400
        # tax (10%) = 240
        # total = 2640

        self.assertAlmostEqual(sale_order.amount_untaxed, 2400.0)
        self.assertAlmostEqual(sale_order.amount_tax, 240.0)
        self.assertAlmostEqual(sale_order.amount_total, 2640.0)
        self.assertAlmostEqual(sale_order.tax_totals['amount_untaxed'], 2400.0)
        self.assertAlmostEqual(sale_order.tax_totals['amount_tax'], 240.0)
        self.assertAlmostEqual(sale_order.tax_totals['amount_total'], 2640.0)

    def test_compute_amounts_and_tax_totals_quantity_based(self):
        """Test amounts and tax totals for a quantity-based product."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_qty.id,
                    'product_uom_qty': 3.0,
                    'price_unit': 100.0,
                    'tax_id': [(6, 0, self.tax_10.ids)],
                })
            ]
        })
        # price = 100, qty = 3 -> subtotal = 300
        # tax (10%) = 30
        # total = 330

        self.assertAlmostEqual(sale_order.amount_untaxed, 300.0)
        self.assertAlmostEqual(sale_order.amount_tax, 30.0)
        self.assertAlmostEqual(sale_order.amount_total, 330.0)
        self.assertAlmostEqual(sale_order.tax_totals['amount_untaxed'], 300.0)
        self.assertAlmostEqual(sale_order.tax_totals['amount_tax'], 30.0)
        self.assertAlmostEqual(sale_order.tax_totals['amount_total'], 330.0)

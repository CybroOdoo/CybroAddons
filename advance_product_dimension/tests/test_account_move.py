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
class TestAccountMove(TransactionCase):
    """
    Test suite for models/account_move.py (AccountMove model).

    Covers:
        - _compute_tax_totals
        - _compute_amounts
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.partner = cls.env['res.partner'].create({'name': 'Test Invoice Customer'})

        cls.tax_10 = cls.env['account.tax'].create({
            'name': 'Tax 10%',
            'amount_type': 'percent',
            'amount': 10.0,
        })

        cls.product_dim = cls.env['product.product'].create({
            'name': 'Dim Product Inv',
            'price_calculation_based_on': 'based_on_dimension',
            'uom_prompt_id': cls.uom_unit.id,
            'list_price': 50.0,
            'taxes_id': [(6, 0, cls.tax_10.ids)],
            'type': 'consu',
        })

        cls.product_qty = cls.env['product.product'].create({
            'name': 'Qty Product Inv',
            'price_calculation_based_on': 'based_on_quantity',
            'list_price': 100.0,
            'taxes_id': [(6, 0, cls.tax_10.ids)],
            'type': 'consu',
        })

    def test_compute_amounts_and_tax_totals_dimension_based(self):
        """Test amounts and tax totals for a dimension-based product."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        self.env['account.move.line'].create({
            'move_id': move.id,
            'product_id': self.product_dim.id,
            'quantity': 2.0,
            'price_unit': 50.0,
            'length': 2.0,
            'width': 3.0,
            'height': 4.0, # dim_qty = 24
            'tax_ids': [(6, 0, self.tax_10.ids)],
        })
        # dim_qty = 24, price = 50 -> base = 1200
        # qty = 2 -> subtotal = 2400
        # tax = 240
        # total = 2640

        self.assertAlmostEqual(move.amount_untaxed, 2400.0)
        self.assertAlmostEqual(move.tax_totals['amount_untaxed'], 2400.0)
        self.assertAlmostEqual(move.tax_totals['amount_tax'], 240.0)
        self.assertAlmostEqual(move.tax_totals['amount_total'], 2640.0)

    def test_compute_amounts_and_tax_totals_quantity_based(self):
        """Test amounts and tax totals for a quantity-based product."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        self.env['account.move.line'].create({
            'move_id': move.id,
            'product_id': self.product_qty.id,
            'quantity': 3.0,
            'price_unit': 100.0,
            'tax_ids': [(6, 0, self.tax_10.ids)],
        })
        # qty = 3, price = 100 -> subtotal = 300
        # tax = 30
        # total = 330

        self.assertAlmostEqual(move.amount_untaxed, 300.0)
        self.assertAlmostEqual(move.amount_tax, 30.0)
        self.assertAlmostEqual(move.amount_total, 330.0)
        self.assertAlmostEqual(move.tax_totals['amount_untaxed'], 300.0)
        self.assertAlmostEqual(move.tax_totals['amount_tax'], 30.0)
        self.assertAlmostEqual(move.tax_totals['amount_total'], 330.0)

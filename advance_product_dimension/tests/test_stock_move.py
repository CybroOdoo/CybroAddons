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
class TestStockMove(TransactionCase):
    """
    Test suite for models/stock_move.py (StockMove model).

    Covers:
        - _compute_dimension_qty
        - _prepare_procurement_values
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.location_src = cls.env.ref('stock.stock_location_suppliers')
        cls.location_dest = cls.env.ref('stock.stock_location_stock')

        cls.product_dim = cls.env['product.product'].create({
            'name': 'Dim Product Stock',
            'price_calculation_based_on': 'based_on_dimension',
            'uom_prompt_id': cls.uom_unit.id,
            'type': 'consu',
        })

    def test_compute_dimension_qty_length_width_height(self):
        """dimension_qty should compute based on dimension_method."""
        move = self.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': self.product_dim.id,
            'product_uom': self.uom_unit.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'length': 2.0,
            'width': 3.0,
            'height': 4.0,
            'dimension_method': 'length_width_height',
        })
        self.assertAlmostEqual(move.dimension_qty, 24.0)

    def test_compute_dimension_qty_length_width(self):
        """dimension_qty should compute based on dimension_method = length_width."""
        move = self.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': self.product_dim.id,
            'product_uom': self.uom_unit.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'length': 2.0,
            'width': 3.0,
            'height': 4.0,
            'dimension_method': 'length_width',
        })
        self.assertAlmostEqual(move.dimension_qty, 6.0)

    def test_prepare_procurement_values(self):
        """_prepare_procurement_values should pass dimensions."""
        move = self.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': self.product_dim.id,
            'product_uom': self.uom_unit.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'length': 2.0,
            'width': 3.0,
            'height': 4.0,
            'dimension_method': 'length_width_height',
        })
        vals = move._prepare_procurement_values()
        self.assertEqual(vals['length'], 2.0)
        self.assertEqual(vals['width'], 3.0)
        self.assertEqual(vals['height'], 4.0)
        self.assertAlmostEqual(vals['dimension_qty'], 24.0)
        self.assertEqual(vals['dimension_method'], 'length_width_height')

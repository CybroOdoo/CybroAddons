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
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install', 'advance_product_dimension')
class TestProductProduct(TransactionCase):
    """
    Test suite for models/product_product.py (ProductProduct model).

    Covers:
        - _onchange_price_calculation_based_on
        - _check_dimension_configuration
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

    # ------------------------------------------------------------------
    # _onchange_price_calculation_based_on
    # ------------------------------------------------------------------

    def test_onchange_price_calculation_based_on_sets_dimension_true(self):
        """Setting 'based_on_dimension' must set use_dimensional_values=True."""
        product = self.env['product.product'].new({
            'name': 'Dim Product',
            'price_calculation_based_on': 'based_on_dimension',
        })
        product._onchange_price_calculation_based_on()
        self.assertTrue(product.use_dimensional_values)

    def test_onchange_price_calculation_based_on_sets_dimension_false(self):
        """Setting 'based_on_quantity' must set use_dimensional_values=False."""
        product = self.env['product.product'].new({
            'name': 'Qty Product',
            'price_calculation_based_on': 'based_on_quantity',
        })
        product.use_dimensional_values = True
        product._onchange_price_calculation_based_on()
        self.assertFalse(product.use_dimensional_values)

    # ------------------------------------------------------------------
    # _check_dimension_configuration
    # ------------------------------------------------------------------

    def test_check_dimension_configuration_raises_without_uom_prompt(self):
        """ValidationError when uom_prompt_id missing for dimension-based product."""
        with self.assertRaises(ValidationError):
            self.env['product.product'].create({
                'name': 'No UOM',
                'price_calculation_based_on': 'based_on_dimension',
                'min_length': 0.0, 'max_length': 5.0,
                'min_width': 0.0, 'max_width': 5.0,
                'min_height': 0.0, 'max_height': 5.0,
            })

    def test_check_dimension_configuration_raises_min_length_gt_max(self):
        """ValidationError when min_length > max_length."""
        with self.assertRaises(ValidationError):
            self.env['product.product'].create({
                'name': 'Bad Length',
                'price_calculation_based_on': 'based_on_dimension',
                'uom_prompt_id': self.uom_unit.id,
                'min_length': 10.0, 'max_length': 5.0,
                'min_width': 0.0, 'max_width': 5.0,
                'min_height': 0.0, 'max_height': 5.0,
            })

    def test_check_dimension_configuration_raises_min_width_gt_max(self):
        """ValidationError when min_width > max_width."""
        with self.assertRaises(ValidationError):
            self.env['product.product'].create({
                'name': 'Bad Width',
                'price_calculation_based_on': 'based_on_dimension',
                'uom_prompt_id': self.uom_unit.id,
                'min_length': 0.0, 'max_length': 5.0,
                'min_width': 10.0, 'max_width': 5.0,
                'min_height': 0.0, 'max_height': 5.0,
            })

    def test_check_dimension_configuration_raises_min_height_gt_max(self):
        """ValidationError when min_height > max_height."""
        with self.assertRaises(ValidationError):
            self.env['product.product'].create({
                'name': 'Bad Height',
                'price_calculation_based_on': 'based_on_dimension',
                'uom_prompt_id': self.uom_unit.id,
                'min_length': 0.0, 'max_length': 5.0,
                'min_width': 0.0, 'max_width': 5.0,
                'min_height': 10.0, 'max_height': 5.0,
            })

    def test_check_dimension_configuration_valid_dimension_product(self):
        """No error for a valid dimension-based product with correct config."""
        product = self.env['product.product'].create({
            'name': 'Valid Dim Product',
            'price_calculation_based_on': 'based_on_dimension',
            'uom_prompt_id': self.uom_unit.id,
            'min_length': 0.0, 'max_length': 10.0,
            'min_width': 0.0, 'max_width': 10.0,
            'min_height': 0.0, 'max_height': 10.0,
        })
        self.assertTrue(product.id)

    def test_check_dimension_configuration_skips_quantity_based(self):
        """No error for quantity-based product even without uom_prompt_id."""
        product = self.env['product.product'].create({
            'name': 'Qty Only',
            'price_calculation_based_on': 'based_on_quantity',
        })
        self.assertTrue(product.id)

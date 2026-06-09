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
class TestSaleOrderLine(TransactionCase):
    """
    Test suite for models/sale_order_line.py (SaleOrderLine model).

    Covers:
        - _get_dimension_method
        - _compute_dimension_qty
        - _compute_amount
        - _onchange_validate_dimensions
        - _validate_dimensions_on_save
        - _prepare_invoice_line
        - _prepare_procurement_values
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})

        # Quantity-based product
        cls.product_qty = cls.env['product.product'].create({
            'name': 'Qty Product',
            'price_calculation_based_on': 'based_on_quantity',
            'list_price': 100.0,
            'type': 'consu',
        })

        # Dimension-based product
        cls.product_dim = cls.env['product.product'].create({
            'name': 'Dim Product',
            'price_calculation_based_on': 'based_on_dimension',
            'uom_prompt_id': cls.uom_unit.id,
            'min_length': 0.0, 'max_length': 100.0,
            'min_width': 0.0, 'max_width': 100.0,
            'min_height': 0.0, 'max_height': 100.0,
            'list_price': 50.0,
            'type': 'consu',
        })

        # Sale order
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def _make_line(self, product, length=0.0, width=0.0, height=0.0, qty=1.0):
        """Helper: create a sale.order.line with given dimensions."""
        return self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': product.id,
            'product_uom_qty': qty,
            'price_unit': product.list_price,
            'length': length,
            'width': width,
            'height': height,
        })

    # ------------------------------------------------------------------
    # _get_dimension_method
    # ------------------------------------------------------------------

    def test_get_dimension_method_length_only(self):
        """_get_dimension_method returns 'length' when only length > 0."""
        line = self.env['sale.order.line'].new({
            'order_id': self.sale_order.id,
            'product_id': self.product_dim.id,
            'length': 5.0, 'width': 0.0, 'height': 0.0,
        })
        self.assertEqual(line._get_dimension_method(), 'length')

    def test_get_dimension_method_length_width(self):
        """_get_dimension_method returns 'length_width' when length and width > 0."""
        line = self.env['sale.order.line'].new({
            'order_id': self.sale_order.id,
            'product_id': self.product_dim.id,
            'length': 5.0, 'width': 3.0, 'height': 0.0,
        })
        self.assertEqual(line._get_dimension_method(), 'length_width')

    def test_get_dimension_method_all_three(self):
        """_get_dimension_method returns 'length_width_height' when all dims > 0."""
        line = self.env['sale.order.line'].new({
            'order_id': self.sale_order.id,
            'product_id': self.product_dim.id,
            'length': 2.0, 'width': 3.0, 'height': 4.0,
        })
        self.assertEqual(line._get_dimension_method(), 'length_width_height')

    def test_get_dimension_method_no_dims(self):
        """_get_dimension_method returns False when no dimension > 0."""
        line = self.env['sale.order.line'].new({
            'order_id': self.sale_order.id,
            'product_id': self.product_dim.id,
            'length': 0.0, 'width': 0.0, 'height': 0.0,
        })
        self.assertFalse(line._get_dimension_method())

    # ------------------------------------------------------------------
    # _compute_dimension_qty
    # ------------------------------------------------------------------

    def test_compute_dimension_qty_for_quantity_based_product(self):
        """dimension_qty must be 0 for a quantity-based product."""
        line = self._make_line(self.product_qty, length=2.0, width=3.0, height=4.0)
        self.assertEqual(line.dimension_qty, 0.0)

    def test_compute_dimension_qty_all_dims_set(self):
        """dimension_qty must equal L×W×H for a dimension-based product."""
        line = self._make_line(self.product_dim, length=2.0, width=3.0, height=4.0)
        self.assertAlmostEqual(line.dimension_qty, 24.0)

    def test_compute_dimension_qty_zero_dims_gives_zero(self):
        """dimension_qty must be 0 when all dimensions are 0."""
        line = self.env['sale.order.line'].new({
            'order_id': self.sale_order.id,
            'product_id': self.product_dim.id,
            'length': 0.0, 'width': 0.0, 'height': 0.0,
        })
        self.assertEqual(line.dimension_qty, 0.0)

    def test_compute_dimension_qty_partial_dims_treats_zero_as_one(self):
        """When one dim is 0, it is treated as 1 in the product."""
        line = self.env['sale.order.line'].new({
            'order_id': self.sale_order.id,
            'product_id': self.product_dim.id,
            'length': 5.0, 'width': 0.0, 'height': 2.0,
        })
        # width=0 → treated as 1; result = 5 * 1 * 2 = 10
        self.assertAlmostEqual(line.dimension_qty, 10.0)

    # ------------------------------------------------------------------
    # _compute_amount
    # ------------------------------------------------------------------

    def test_compute_amount_quantity_based_product(self):
        """price_subtotal for qty-based product = price_unit * qty."""
        line = self._make_line(self.product_qty, qty=3.0)
        self.assertAlmostEqual(line.price_subtotal, 300.0)

    def test_compute_amount_dimension_based_product(self):
        """price_subtotal for dim-based product = dimension_qty * price_unit * qty."""
        # price_unit=50, L=2, W=3, H=4 → dim_qty=24 → subtotal = 24 * 50 * 1 = 1200
        line = self._make_line(self.product_dim, length=2.0, width=3.0, height=4.0, qty=1.0)
        self.assertAlmostEqual(line.price_subtotal, 1200.0, places=2)

    # ------------------------------------------------------------------
    # _onchange_validate_dimensions
    # ------------------------------------------------------------------

    def test_onchange_validate_dimensions_raises_for_qty_product_with_dims(self):
        """ValidationError when dimensions set on a quantity-based product."""
        line = self.env['sale.order.line'].new({
            'order_id': self.sale_order.id,
            'product_id': self.product_qty.id,
            'length': 5.0,
        })
        with self.assertRaises(ValidationError):
            line._onchange_validate_dimensions()

    def test_onchange_validate_dimensions_no_error_for_dim_product_valid_dims(self):
        """No error when dimension-based product has dimensions within range."""
        line = self.env['sale.order.line'].new({
            'order_id': self.sale_order.id,
            'product_id': self.product_dim.id,
            'length': 5.0, 'width': 5.0, 'height': 5.0,
        })
        try:
            line._onchange_validate_dimensions()
        except ValidationError as e:
            self.fail(f"Unexpected ValidationError: {e}")

    def test_onchange_validate_dimensions_no_error_when_no_product(self):
        """No error when no product is set on the line."""
        line = self.env['sale.order.line'].new({
            'order_id': self.sale_order.id,
            'length': 5.0,
        })
        try:
            line._onchange_validate_dimensions()
        except ValidationError as e:
            self.fail(f"Unexpected ValidationError: {e}")

    # ------------------------------------------------------------------
    # _validate_dimensions_on_save
    # ------------------------------------------------------------------

    def test_validate_dimensions_on_save_raises_zero_length(self):
        """ValidationError when length=0 for a dimension-based product on save."""
        with self.assertRaises(ValidationError):
            self.env['sale.order.line'].create({
                'order_id': self.sale_order.id,
                'product_id': self.product_dim.id,
                'product_uom_qty': 1.0,
                'price_unit': 50.0,
                'length': 0.0, 'width': 5.0, 'height': 5.0,
            })

    def test_validate_dimensions_on_save_raises_zero_width(self):
        """ValidationError when width=0 for a dimension-based product on save."""
        with self.assertRaises(ValidationError):
            self.env['sale.order.line'].create({
                'order_id': self.sale_order.id,
                'product_id': self.product_dim.id,
                'product_uom_qty': 1.0,
                'price_unit': 50.0,
                'length': 5.0, 'width': 0.0, 'height': 5.0,
            })

    def test_validate_dimensions_on_save_raises_zero_height(self):
        """ValidationError when height=0 for a dimension-based product on save."""
        with self.assertRaises(ValidationError):
            self.env['sale.order.line'].create({
                'order_id': self.sale_order.id,
                'product_id': self.product_dim.id,
                'product_uom_qty': 1.0,
                'price_unit': 50.0,
                'length': 5.0, 'width': 5.0, 'height': 0.0,
            })

    def test_validate_dimensions_on_save_no_error_for_qty_product(self):
        """No error for quantity-based product even with zero dimensions."""
        try:
            line = self._make_line(self.product_qty)
            self.assertTrue(line.id)
        except ValidationError as e:
            self.fail(f"Unexpected ValidationError: {e}")

    # ------------------------------------------------------------------
    # _prepare_invoice_line
    # ------------------------------------------------------------------

    def test_prepare_invoice_line_contains_dimension_fields(self):
        """_prepare_invoice_line must include length, width, height, dimension_qty."""
        line = self._make_line(self.product_dim, length=2.0, width=3.0, height=4.0)
        result = line._prepare_invoice_line()
        self.assertIn('length', result)
        self.assertIn('width', result)
        self.assertIn('height', result)
        self.assertIn('dimension_qty', result)
        self.assertEqual(result['length'], 2.0)
        self.assertEqual(result['width'], 3.0)
        self.assertEqual(result['height'], 4.0)

    def test_prepare_invoice_line_dimension_qty_value(self):
        """_prepare_invoice_line dimension_qty must match computed value."""
        line = self._make_line(self.product_dim, length=2.0, width=3.0, height=4.0)
        result = line._prepare_invoice_line()
        self.assertAlmostEqual(result['dimension_qty'], 24.0)

    # ------------------------------------------------------------------
    # _prepare_procurement_values
    # ------------------------------------------------------------------

    def test_prepare_procurement_values_contains_dimension_fields(self):
        """_prepare_procurement_values must include length, width, height, dimension_qty, dimension_method."""
        line = self._make_line(self.product_dim, length=2.0, width=3.0, height=4.0)
        result = line._prepare_procurement_values()
        self.assertIn('length', result)
        self.assertIn('width', result)
        self.assertIn('height', result)
        self.assertIn('dimension_qty', result)
        self.assertIn('dimension_method', result)

    def test_prepare_procurement_values_correct_dimension_values(self):
        """_prepare_procurement_values must carry the correct dimension values."""
        line = self._make_line(self.product_dim, length=2.0, width=3.0, height=4.0)
        result = line._prepare_procurement_values()
        self.assertEqual(result['length'], 2.0)
        self.assertEqual(result['width'], 3.0)
        self.assertEqual(result['height'], 4.0)
        self.assertAlmostEqual(result['dimension_qty'], 24.0)

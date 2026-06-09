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
class TestPurchaseOrderLine(TransactionCase):
    """
    Test suite for models/purchase_order_line.py (PurchaseOrderLine model).

    Covers:
        - _get_dimension_values_from_procurement
        - _compute_dimension_qty
        - _compute_amount
        - _onchange_validate_dimensions
        - _validate_dimensions_on_save
        - _prepare_account_move_line
        - _prepare_purchase_order_line_from_procurement
        - _find_candidate
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.partner = cls.env['res.partner'].create({'name': 'Test Vendor'})

        # Quantity-based product
        cls.product_qty = cls.env['product.product'].create({
            'name': 'Qty Product PO',
            'price_calculation_based_on': 'based_on_quantity',
            'list_price': 100.0,
            'type': 'consu',
        })

        # Dimension-based product
        cls.product_dim = cls.env['product.product'].create({
            'name': 'Dim Product PO',
            'price_calculation_based_on': 'based_on_dimension',
            'uom_prompt_id': cls.uom_unit.id,
            'min_length': 0.0, 'max_length': 100.0,
            'min_width': 0.0, 'max_width': 100.0,
            'min_height': 0.0, 'max_height': 100.0,
            'list_price': 50.0,
            'type': 'consu',
        })

        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })

    def _make_line(self, product, length=0.0, width=0.0, height=0.0, qty=1.0):
        return self.env['purchase.order.line'].create({
            'order_id': self.purchase_order.id,
            'product_id': product.id,
            'product_qty': qty,
            'price_unit': product.list_price,
            'length': length,
            'width': width,
            'height': height,
        })

    def test_compute_dimension_qty(self):
        """dimension_qty should compute correctly based on L*W*H."""
        line = self._make_line(self.product_dim, length=2.0, width=3.0, height=4.0)
        self.assertAlmostEqual(line.dimension_qty, 24.0)

    def test_compute_amount_dimension_based(self):
        """price_subtotal should use dimension_qty for dimension-based product."""
        # dim_qty=24, price_unit=50 -> base_price=1200 -> qty=2 -> subtotal=2400
        line = self._make_line(self.product_dim, length=2.0, width=3.0, height=4.0, qty=2.0)
        self.assertAlmostEqual(line.price_subtotal, 2400.0)

    def test_onchange_validate_dimensions_qty_based(self):
        """Setting dimensions on a qty-based product should raise ValidationError."""
        line = self.env['purchase.order.line'].new({
            'order_id': self.purchase_order.id,
            'product_id': self.product_qty.id,
            'length': 5.0,
        })
        with self.assertRaises(ValidationError):
            line._onchange_validate_dimensions()

    def test_validate_dimensions_on_save_zero_length(self):
        """ValidationError when length=0 for a dimension-based product on save."""
        with self.assertRaises(ValidationError):
            self.env['purchase.order.line'].create({
                'order_id': self.purchase_order.id,
                'product_id': self.product_dim.id,
                'product_qty': 1.0,
                'length': 0.0, 'width': 5.0, 'height': 5.0,
            })

    def test_prepare_account_move_line(self):
        """Account move line values should include dimension data."""
        line = self._make_line(self.product_dim, length=2.0, width=3.0, height=4.0)
        move_vals = line._prepare_account_move_line()
        self.assertEqual(move_vals['length'], 2.0)
        self.assertEqual(move_vals['width'], 3.0)
        self.assertEqual(move_vals['height'], 4.0)
        self.assertAlmostEqual(move_vals['dimension_qty'], 24.0)

    def test_get_dimension_values_from_procurement(self):
        """Should correctly extract dimensions from procurement values."""
        vals = {'length': 2.0, 'width': 3.0, 'height': 4.0, 'dimension_qty': 24.0}
        res = self.env['purchase.order.line'].new()._get_dimension_values_from_procurement(vals)
        self.assertEqual(res['length'], 2.0)
        self.assertEqual(res['width'], 3.0)
        self.assertEqual(res['height'], 4.0)
        self.assertEqual(res['dimension_qty'], 24.0)

    def test_prepare_purchase_order_line_from_procurement(self):
        """Should copy dimensions from procurement to PO line."""
        supplier = self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_tmpl_id': self.product_dim.product_tmpl_id.id,
        })
        vals = {'length': 2.0, 'width': 3.0, 'height': 4.0, 'dimension_qty': 24.0, 'supplier': supplier}
        res = self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
            self.product_dim, 1.0, self.uom_unit, self.env.company, vals, self.purchase_order
        )
        self.assertEqual(res['length'], 2.0)
        self.assertEqual(res['width'], 3.0)
        self.assertEqual(res['height'], 4.0)
        self.assertEqual(res['dimension_qty'], 24.0)



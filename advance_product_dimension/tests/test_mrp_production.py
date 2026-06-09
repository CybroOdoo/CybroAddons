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
class TestMrpProduction(TransactionCase):
    """
    Test suite for models/mrp_production.py (MrpProduction model).

    Covers:
        - _compute_show_dimension_fields
        - _compute_dimension_qty
        - _onchange_product_id
        - _onchange_validate_dimensions
        - _validate_dimensions_on_save
        - action_confirm (validation)
        - create_sale_order_mo
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        cls.product_qty = cls.env['product.product'].create({
            'name': 'Qty Product MRP',
            'price_calculation_based_on': 'based_on_quantity',
            'type': 'product',
        })

        cls.product_dim = cls.env['product.product'].create({
            'name': 'Dim Product MRP',
            'price_calculation_based_on': 'based_on_dimension',
            'uom_prompt_id': cls.uom_unit.id,
            'min_length': 0.0, 'max_length': 100.0,
            'min_width': 0.0, 'max_width': 100.0,
            'min_height': 0.0, 'max_height': 100.0,
            'type': 'product',
        })

        cls.bom_dim = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_dim.product_tmpl_id.id,
            'product_qty': 1.0,
            'bom_line_ids': [
                (0, 0, {'product_id': cls.product_qty.id, 'product_qty': 1.0})
            ]
        })

    def test_compute_show_dimension_fields(self):
        """Should show dimension fields only for dimension-based products."""
        mo_dim = self.env['mrp.production'].new({'product_id': self.product_dim.id})
        mo_dim._compute_show_dimension_fields()
        self.assertTrue(mo_dim.show_dimension_fields)

        mo_qty = self.env['mrp.production'].new({'product_id': self.product_qty.id})
        mo_qty._compute_show_dimension_fields()
        self.assertFalse(mo_qty.show_dimension_fields)

    def test_compute_dimension_qty_length_width_height(self):
        """Should correctly compute dimension quantity."""
        mo = self.env['mrp.production'].new({
            'product_id': self.product_dim.id,
            'length': 2.0, 'width': 3.0, 'height': 4.0,
            'dimension_method': 'length_width_height',
        })
        mo._compute_dimension_qty()
        self.assertAlmostEqual(mo.dimension_qty, 24.0)

    def test_onchange_product_id_sets_defaults(self):
        """Should initialize defaults when changing to dimension-based product."""
        mo = self.env['mrp.production'].new({'product_id': self.product_dim.id})
        mo._onchange_product_id()
        self.assertEqual(mo.dimension_method, 'length_width_height')
        self.assertEqual(mo.length, 0.0)

    def test_validate_dimensions_on_save_qty_product(self):
        """Should pass validation for qty-based products."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_qty.id,
            'product_qty': 1.0,
            'bom_id': self.bom_dim.id, # using a dummy bom
        })
        self.assertTrue(mo.id)

    def test_validate_dimensions_on_save_dim_product_missing_method(self):
        """Should raise if method is missing."""
        with self.assertRaises(ValidationError):
            self.env['mrp.production'].create({
                'product_id': self.product_dim.id,
                'product_qty': 1.0,
                'bom_id': self.bom_dim.id,
                'dimension_method': False,
            })

    def test_validate_dimensions_on_save_dim_product_zero_length(self):
        """Should raise if length is zero for length_width_height."""
        with self.assertRaises(ValidationError):
            self.env['mrp.production'].create({
                'product_id': self.product_dim.id,
                'product_qty': 1.0,
                'bom_id': self.bom_dim.id,
                'dimension_method': 'length_width_height',
                'length': 0.0, 'width': 3.0, 'height': 4.0,
            })

    def test_action_confirm_validates_dimensions(self):
        """Should validate dimension values strictly > 0 on confirm."""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_dim.id,
            'product_qty': 1.0,
            'bom_id': self.bom_dim.id,
            'dimension_method': 'length',
            'length': 5.0, # width and height default to 0.0, which is allowed for 'length' method here
        })
        # Mock negative length on purpose
        mo.length = -1.0
        with self.assertRaises(ValidationError):
            mo.action_confirm()

    def test_create_sale_order_mo(self):
        """Should populate dimensions from a pseudo sale order line."""
        class MockSOLine:
            length = 5.0
            width = 4.0
            height = 3.0
            dimension_qty = 60.0

        mo = self.env['mrp.production'].new()
        mo.create_sale_order_mo(MockSOLine())
        self.assertEqual(mo.length, 5.0)
        self.assertEqual(mo.width, 4.0)
        self.assertEqual(mo.height, 3.0)

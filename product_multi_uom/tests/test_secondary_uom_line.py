# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for secondary.uom.line model in product_multi_uom."""
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSecondaryUomLine(TransactionCase):
    """Test cases for secondary.uom.line model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        if not cls.uom_unit:
            cls.uom_unit = cls.env['uom.uom'].create({
                'name': 'Test Base Unit Line',
                'relative_factor': 1.0,
            })
        cls.uom_pack_5 = cls.env['uom.uom'].create({
            'name': 'Test Pack of 5',
            'relative_uom_id': cls.uom_unit.id,
            'relative_factor': 5.0,
        })
        cls.uom_pack_10 = cls.env['uom.uom'].create({
            'name': 'Test Pack of 10 Line',
            'relative_uom_id': cls.uom_unit.id,
            'relative_factor': 10.0,
        })
        cls.template = cls.env['product.template'].create({
            'name': 'Test Template For Line',
            'uom_id': cls.uom_unit.id,
            'is_need_secondary_uom': True,
        })
        cls.product = cls.template.product_variant_ids[0]

    def test_create_secondary_uom_line(self):
        """Test creating a secondary.uom.line linked to a template and product."""
        line = self.env['secondary.uom.line'].create({
            'secondary_uom_id': self.uom_pack_5.id,
            'product_template_id': self.template.id,
            'secondary_uom_ratio': 5.0,
            'example_ratio': f" 1 {self.uom_pack_5.name} = 5.0 {self.uom_unit.name}",
        })
        self.assertEqual(line.secondary_uom_id, self.uom_pack_5)
        self.assertEqual(line.product_template_id, self.template)
        self.assertEqual(line.secondary_uom_ratio, 5.0)

    def test_compute_uom_ids_with_context(self):
        """Test _compute_uom_ids filters based on parent_uom_id and selected_uom_ids in context."""
        line = self.env['secondary.uom.line'].create({
            'secondary_uom_id': self.uom_pack_5.id,
            'product_template_id': self.template.id,
        })
        context = {
            'parent_uom_id': self.uom_unit.id,
            'selected_uom_ids': [self.uom_pack_10.id],
        }
        line_with_ctx = line.with_context(**context)
        line_with_ctx._compute_uom_ids()

        self.assertIn(self.uom_unit, line_with_ctx.uom_ids)
        self.assertIn(self.uom_pack_5, line_with_ctx.uom_ids)
        self.assertNotIn(self.uom_pack_10, line_with_ctx.uom_ids)

    def test_onchange_secondary_uom_id_updates_ratio_and_example(self):
        """Test _onchange_secondary_uom_id sets default relative factor and allows custom ratio."""
        line = self.env['secondary.uom.line'].create({
            'secondary_uom_id': self.uom_pack_5.id,
            'product_template_id': self.template.id,
        })
        line.secondary_uom_id = self.uom_pack_10
        line._onchange_secondary_uom_id()
        line._onchange_secondary_uom_ratio()

        self.assertEqual(line.secondary_uom_ratio, 10.0)
        self.assertIn(self.uom_pack_10.name, line.example_ratio)
        self.assertIn(self.uom_unit.name, line.example_ratio)

        # Ensure custom ratio is preserved when user changes it
        line.secondary_uom_ratio = 8.5
        line._onchange_secondary_uom_ratio()
        self.assertEqual(line.secondary_uom_ratio, 8.5)
        self.assertIn('8.5', line.example_ratio)

    def test_check_unique_secondary_uom_constraint(self):
        """Test that duplicate secondary UoM on same product raises ValidationError."""
        self.env['secondary.uom.line'].create({
            'secondary_uom_id': self.uom_pack_5.id,
            'product_id': self.product.id,
            'secondary_uom_ratio': 5.0,
        })
        with self.assertRaises(ValidationError):
            self.env['secondary.uom.line'].create({
                'secondary_uom_id': self.uom_pack_5.id,
                'product_id': self.product.id,
                'secondary_uom_ratio': 5.0,
            })

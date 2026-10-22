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
"""Test suite for duplicate_product_bom module."""
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDuplicateProductBom(TransactionCase):
    """Unit tests for duplicating product templates with BOMs."""

    @classmethod
    def setUpClass(cls):
        """Set up component products, templates, and BOMs."""
        super().setUpClass()
        cls.component_a = cls.env['product.product'].create({
            'name': 'Component A',
            'type': 'consu',
        })
        cls.component_b = cls.env['product.product'].create({
            'name': 'Component B',
            'type': 'consu',
        })

        # Single-variant product template with a standard BOM
        cls.template_single = cls.env['product.template'].create({
            'name': 'Manufactured Desk',
            'type': 'consu',
        })
        cls.bom_single = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.template_single.id,
            'code': 'BOM-DESK-01',
            'product_qty': 1.0,
            'bom_line_ids': [
                (0, 0, {'product_id': cls.component_a.id, 'product_qty': 2.0}),
                (0, 0, {'product_id': cls.component_b.id, 'product_qty': 4.0}),
            ],
        })

    def test_01_single_product_bom_duplication(self):
        """Test duplicating a single product template duplicates its BOM."""
        copied_template = self.template_single.copy()

        self.assertEqual(
            len(copied_template.bom_ids), 1,
            "Copied product template should have exactly one BOM."
        )
        copied_bom = copied_template.bom_ids[0]
        self.assertEqual(
            copied_bom.product_tmpl_id, copied_template,
            "Copied BOM must point to the new product template."
        )
        self.assertFalse(
            copied_bom.product_id,
            "Template-level BOM should not have a variant product_id set."
        )
        self.assertEqual(
            len(copied_bom.bom_line_ids), 2,
            "Copied BOM must have the same number of BOM lines."
        )
        self.assertEqual(
            set(copied_bom.bom_line_ids.mapped('product_id')),
            {self.component_a, self.component_b},
            "Copied BOM lines should match original components."
        )
        self.assertEqual(
            self.template_single.bom_ids, self.bom_single,
            "Original product template's BOM should remain unchanged."
        )

    def test_02_multi_record_copy_duplication(self):
        """Test copying multiple product template records in a single call."""
        template_two = self.env['product.template'].create({
            'name': 'Manufactured Chair',
            'type': 'consu',
        })
        bom_two = self.env['mrp.bom'].create({
            'product_tmpl_id': template_two.id,
            'code': 'BOM-CHAIR-01',
            'product_qty': 1.0,
            'bom_line_ids': [
                (0, 0, {'product_id': self.component_a.id, 'product_qty': 1.0}),
            ],
        })

        templates = self.template_single | template_two
        copied_templates = templates.copy()

        self.assertEqual(
            len(copied_templates), 2,
            "Multi-record copy should return the same number of copied records."
        )

        copy_1 = copied_templates.filtered(
            lambda t: t.name == self.template_single.name or self.template_single.name in t.name
        )[0]
        copy_2 = copied_templates.filtered(
            lambda t: t.name == template_two.name or template_two.name in t.name
        )[0]

        self.assertEqual(
            len(copy_1.bom_ids), 1,
            "First copied template should have one duplicated BOM."
        )
        self.assertEqual(
            copy_1.bom_ids.product_tmpl_id, copy_1,
            "First copied BOM should link to the first copied template."
        )
        self.assertEqual(
            len(copy_2.bom_ids), 1,
            "Second copied template should have one duplicated BOM."
        )
        self.assertEqual(
            copy_2.bom_ids.product_tmpl_id, copy_2,
            "Second copied BOM should link to the second copied template."
        )
        self.assertNotEqual(
            copy_1.bom_ids.id, self.bom_single.id,
            "Copied BOM should be a distinct record from the original."
        )
        self.assertNotEqual(
            copy_2.bom_ids.id, bom_two.id,
            "Copied BOM should be a distinct record from the original."
        )

    def test_03_multiple_boms_duplication(self):
        """Test duplicating a product template with multiple BOMs."""
        template_multi_bom = self.env['product.template'].create({
            'name': 'Custom Table',
            'type': 'consu',
        })
        self.env['mrp.bom'].create({
            'product_tmpl_id': template_multi_bom.id,
            'code': 'BOM-TABLE-STANDARD',
            'product_qty': 1.0,
            'bom_line_ids': [
                (0, 0, {'product_id': self.component_a.id, 'product_qty': 4.0}),
            ],
        })
        self.env['mrp.bom'].create({
            'product_tmpl_id': template_multi_bom.id,
            'code': 'BOM-TABLE-PREMIUM',
            'product_qty': 1.0,
            'bom_line_ids': [
                (0, 0, {'product_id': self.component_b.id, 'product_qty': 4.0}),
            ],
        })

        self.assertEqual(len(template_multi_bom.bom_ids), 2)
        copied_template = template_multi_bom.copy()

        self.assertEqual(
            len(copied_template.bom_ids), 2,
            "Copied template should duplicate all associated BOMs."
        )
        for bom in copied_template.bom_ids:
            self.assertEqual(
                bom.product_tmpl_id, copied_template,
                "Each duplicated BOM must be linked to the new template."
            )

    def test_04_variant_specific_bom_duplication(self):
        """Test that variant-specific BOMs remap product_id to the new variant."""
        color_attribute = self.env['product.attribute'].create({
            'name': 'Color Test BOM',
            'sequence': 1,
        })
        val_red = self.env['product.attribute.value'].create({
            'name': 'Red Test BOM',
            'attribute_id': color_attribute.id,
        })
        val_blue = self.env['product.attribute.value'].create({
            'name': 'Blue Test BOM',
            'attribute_id': color_attribute.id,
        })

        template_with_variants = self.env['product.template'].create({
            'name': 'Configurable Bike',
            'type': 'consu',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': color_attribute.id,
                    'value_ids': [(6, 0, [val_red.id, val_blue.id])],
                }),
            ],
        })

        self.assertEqual(len(template_with_variants.product_variant_ids), 2)
        red_variant = template_with_variants.product_variant_ids.filtered(
            lambda v: val_red in v.product_template_variant_value_ids.product_attribute_value_id
        )

        variant_bom = self.env['mrp.bom'].create({
            'product_tmpl_id': template_with_variants.id,
            'product_id': red_variant.id,
            'code': 'BOM-BIKE-RED',
            'product_qty': 1.0,
            'bom_line_ids': [
                (0, 0, {'product_id': self.component_a.id, 'product_qty': 1.0}),
            ],
        })

        copied_template = template_with_variants.copy()

        self.assertEqual(
            len(copied_template.bom_ids), 1,
            "Copied template should have one duplicated BOM."
        )
        copied_bom = copied_template.bom_ids[0]
        self.assertNotEqual(
            copied_bom.id, variant_bom.id,
            "Copied BOM should be a distinct record from the original variant BOM."
        )
        self.assertEqual(
            copied_bom.product_tmpl_id, copied_template,
            "Copied BOM must point to the new product template."
        )
        self.assertTrue(
            copied_bom.product_id,
            "Variant-specific BOM must retain a variant product_id on the copy."
        )
        self.assertNotEqual(
            copied_bom.product_id, red_variant,
            "Copied BOM must NOT retain the original template's variant product_id."
        )
        self.assertEqual(
            copied_bom.product_id.product_tmpl_id, copied_template,
            "Copied BOM variant product_id must belong to the new product template."
        )
        self.assertIn(
            val_red,
            copied_bom.product_id.product_template_variant_value_ids.product_attribute_value_id,
            "Copied BOM variant must correspond to the matching attribute value (Red)."
        )

    def test_05_product_template_without_bom(self):
        """Test duplicating a product template without BOMs works without errors."""
        template_no_bom = self.env['product.template'].create({
            'name': 'Plain Widget',
            'type': 'consu',
        })
        self.assertEqual(len(template_no_bom.bom_ids), 0)

        copied_template = template_no_bom.copy()
        self.assertEqual(len(copied_template.bom_ids), 0)

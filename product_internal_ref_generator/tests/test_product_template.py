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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Tests for the internal reference of product templates."""
from odoo.tests import tagged

from .common import SEQUENCE_NUMBER, InternalRefCommon


@tagged('post_install', '-at_install')
class TestProductTemplate(InternalRefCommon):
    """Internal reference generation on product templates."""

    def _create_template(self, **vals):
        values = {
            'name': 'Office Chair',
            'type': 'consu',
            'categ_id': self.category.id,
        }
        values.update(vals)
        return self.env['product.template'].create(values)

    def test_01_auto_generate_all_parts(self):
        """Type, name, category and attribute values form the reference."""
        template = self._create_template(attribute_line_ids=[(0, 0, {
            'attribute_id': self.attribute.id,
            'value_ids': [(6, 0, [self.value_red.id, self.value_blue.id])],
        })])
        self.assertRegex(template.default_code,
                         r'^Goods:Off-Fur_Re/Bl/' + SEQUENCE_NUMBER)
        self.assertEqual(template.product_variant_id.default_code,
                         template.default_code)

    def test_02_variants_get_their_attribute_values(self):
        """Each variant gets its own attribute values in its reference."""
        template = self._create_template(name='Desk', attribute_line_ids=[
            (0, 0, {
                'attribute_id': self.size.id,
                'value_ids': [(6, 0, [self.size_small.id,
                                      self.size_large.id])],
            })])
        variants = template.product_variant_ids
        self.assertEqual(len(variants), 2)
        small = variants.filtered(
            lambda variant: 'Small' in variant.display_name)
        large = variants - small
        self.assertRegex(small.default_code,
                         r'^Goods:Des-Fur_Sm/' + SEQUENCE_NUMBER)
        self.assertRegex(large.default_code,
                         r'^Goods:Des-Fur_La/' + SEQUENCE_NUMBER)

    def test_03_single_shared_counter(self):
        """Products and variants share one counter: no number repeats."""
        template = self._create_template(attribute_line_ids=[(0, 0, {
            'attribute_id': self.size.id,
            'value_ids': [(6, 0, [self.size_small.id, self.size_large.id])],
        })])
        single = self._create_template(name='Lamp')
        variant = self.env['product.product'].create({'name': 'Pen'})
        codes = (template.product_variant_ids | single.product_variant_id
                 | variant).mapped('default_code')
        numbers = [code[-5:] for code in codes]
        self.assertEqual(len(set(numbers)), 4)

    def test_04_type_prefixes(self):
        """Service and combo products get their own prefix."""
        self.set_config(product_name_config=False, pro_categ_config=False)
        service = self._create_template(type='service')
        self.assertRegex(service.default_code, r'^Service:' + SEQUENCE_NUMBER)
        combo_choice = self.env['product.combo'].create({
            'name': 'Chair Choice',
            'combo_item_ids': [(0, 0, {
                'product_id': service.product_variant_id.id,
            })],
        })
        combo = self._create_template(
            type='combo', combo_ids=[(6, 0, combo_choice.ids)])
        self.assertRegex(combo.default_code, r'^Combo:' + SEQUENCE_NUMBER)

    def test_05_disabled_parts_only_sequence(self):
        """With every part disabled, only the type and number are used."""
        self.set_config(product_name_config=False, pro_categ_config=False,
                        pro_template_config=False)
        template = self._create_template(attribute_line_ids=[(0, 0, {
            'attribute_id': self.attribute.id,
            'value_ids': [(6, 0, [self.value_red.id])],
        })])
        self.assertRegex(template.default_code, r'^Goods:' + SEQUENCE_NUMBER)

    def test_06_given_reference_is_kept(self):
        """A reference given on creation is never overwritten."""
        templates = self.env['product.template'].create([
            {'name': 'Desk', 'default_code': 'DESK-01'},
            {'name': 'Lamp'},
        ])
        self.assertEqual(templates[0].default_code, 'DESK-01')
        self.assertEqual(templates[0].product_variant_id.default_code,
                         'DESK-01')
        self.assertRegex(templates[1].default_code, r'^Goods:Lam-')

    def test_07_auto_generate_disabled(self):
        """No reference is generated when the option is disabled."""
        self.set_config(auto_generate_internal_ref=False)
        template = self._create_template()
        self.assertFalse(template.default_code)

    def test_08_action_generate_internal_ref(self):
        """The server action fills every variant without a reference."""
        self.set_config(auto_generate_internal_ref=False)
        template = self._create_template(name='Manual Table',
                                         attribute_line_ids=[(0, 0, {
            'attribute_id': self.size.id,
            'value_ids': [(6, 0, [self.size_small.id, self.size_large.id])],
        })])
        existing = self._create_template(name='Sofa', default_code='SOFA')
        action = self.env.ref(
            'product_internal_ref_generator.action_generate_internal_ref')
        action.with_context(
            active_model='product.template',
            active_ids=(template | existing).ids,
        ).run()
        codes = template.product_variant_ids.mapped('default_code')
        self.assertEqual(len(set(codes)), 2)
        for code in codes:
            self.assertRegex(code,
                             r'^Goods:Man-Fur_(Sm|La)/' + SEQUENCE_NUMBER)
        self.assertEqual(existing.default_code, 'SOFA')

    def test_09_action_without_active_ids(self):
        """The action does nothing when no record is selected."""
        self.assertIsNone(
            self.env['product.template'].action_generate_internal_ref())

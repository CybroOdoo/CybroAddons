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
"""Tests for the internal reference of product variants."""
from odoo.tests import tagged

from .common import SEQUENCE_NUMBER, InternalRefCommon


@tagged('post_install', '-at_install')
class TestProductProduct(InternalRefCommon):
    """Internal reference generation on product variants."""

    def _create_product(self, **vals):
        values = {
            'name': 'Service Plan',
            'type': 'service',
            'categ_id': self.category.id,
        }
        values.update(vals)
        return self.env['product.product'].create(values)

    def test_01_auto_generate(self):
        """Type, name and category form the variant reference."""
        product = self._create_product()
        self.assertRegex(product.default_code,
                         r'^Service:Ser-Fur_' + SEQUENCE_NUMBER)

    def test_02_given_reference_is_kept(self):
        """A reference given on creation is never overwritten."""
        product = self._create_product(default_code='PLAN-01')
        self.assertEqual(product.default_code, 'PLAN-01')

    def test_03_auto_generate_disabled(self):
        """No reference is generated when the option is disabled."""
        self.set_config(auto_generate_internal_ref=False)
        product = self._create_product()
        self.assertFalse(product.default_code)

    def test_04_action_generate_internal_ref_pro(self):
        """The variant action uses the variant's own attribute values and
        fills only the variants without reference."""
        self.set_config(auto_generate_internal_ref=False,
                        pro_categ_config=False)
        template = self.env['product.template'].create({
            'name': 'Manual Product',
            'attribute_line_ids': [(0, 0, {
                'attribute_id': self.size.id,
                'value_ids': [(6, 0, [self.size_small.id,
                                      self.size_large.id])],
            })],
        })
        existing = self._create_product(default_code='KEEP')
        variants = template.product_variant_ids
        action = self.env.ref(
            'product_internal_ref_generator.action_generate_internal_ref_pro')
        action.with_context(
            active_model='product.product',
            active_ids=(variants | existing).ids,
        ).run()
        self.assertEqual(
            sorted(code[:-5] for code in variants.mapped('default_code')),
            ['Goods:Man-La/', 'Goods:Man-Sm/'])
        self.assertEqual(existing.default_code, 'KEEP')

    def test_05_action_without_active_ids(self):
        """The action does nothing when no record is selected."""
        self.assertIsNone(
            self.env['product.product'].action_generate_internal_ref_pro())

    def test_06_default_digits_and_separators(self):
        """Unset digit and separator settings fall back to 3 and '-'."""
        for key in ('pro_name_digit', 'pro_name_separator',
                    'pro_categ_digit', 'pro_categ_separator'):
            self.config_parameter.search(
                [('key', '=', 'product_internal_ref_generator.' + key)]
            ).unlink()
        product = self._create_product(name='Consulting')
        self.assertRegex(product.default_code,
                         r'^Service:Con-Fur-' + SEQUENCE_NUMBER)

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
"""Test suite for product.template extension in product_multi_uom."""
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Test cases for product.template extension with secondary UoM."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        if not cls.uom_unit:
            cls.uom_unit = cls.env['uom.uom'].create({
                'name': 'Test Base Unit',
                'relative_factor': 1.0,
            })
        cls.uom_pack = cls.env['uom.uom'].create({
            'name': 'Test Pack of 10',
            'relative_uom_id': cls.uom_unit.id,
            'relative_factor': 10.0,
        })

    def test_product_template_create_with_secondary_uom(self):
        """Test creating a product template with is_need_secondary_uom=True propagates to variants."""
        template = self.env['product.template'].create({
            'name': 'Test Multi UoM Template',
            'uom_id': self.uom_unit.id,
            'is_need_secondary_uom': True,
        })
        self.assertTrue(template.is_need_secondary_uom)
        self.assertTrue(all(variant.is_need_secondary_uom for variant in template.product_variant_ids))

    def test_product_template_create_without_secondary_uom(self):
        """Test creating a product template with is_need_secondary_uom=False does not enable on variants."""
        template = self.env['product.template'].create({
            'name': 'Test Single UoM Template',
            'uom_id': self.uom_unit.id,
            'is_need_secondary_uom': False,
        })
        self.assertFalse(template.is_need_secondary_uom)
        self.assertFalse(any(variant.is_need_secondary_uom for variant in template.product_variant_ids))

    def test_compute_selected_uom_ids(self):
        """Test _compute_selected_uom_ids reflects secondary_uom_ids accurately."""
        template = self.env['product.template'].create({
            'name': 'Test Selected UoMs Template',
            'uom_id': self.uom_unit.id,
            'is_need_secondary_uom': True,
            'secondary_uom_ids': [
                fields.Command.create({
                    'secondary_uom_id': self.uom_unit.id,
                    'secondary_uom_ratio': 1.0,
                }),
                fields.Command.create({
                    'secondary_uom_id': self.uom_pack.id,
                    'secondary_uom_ratio': 10.0,
                }),
            ],
        })
        self.assertEqual(len(template.selected_uom_ids), 2)
        self.assertIn(self.uom_unit, template.selected_uom_ids)
        self.assertIn(self.uom_pack, template.selected_uom_ids)

        template.secondary_uom_ids = [fields.Command.clear()]
        self.assertEqual(len(template.selected_uom_ids), 0)

    def test_onchange_is_need_secondary_uom(self):
        """Test _onchange_is_need_secondary_uom populates default base and relative UoMs."""
        template = self.env['product.template'].create({
            'name': 'Test Onchange Template',
            'uom_id': self.uom_unit.id,
            'is_need_secondary_uom': True,
        })
        template._onchange_is_need_secondary_uom()
        secondary_uoms = template.secondary_uom_ids.mapped('secondary_uom_id')
        self.assertIn(self.uom_unit, secondary_uoms)
        self.assertIn(self.uom_pack, secondary_uoms)

        pack_line = template.secondary_uom_ids.filtered(lambda line: line.secondary_uom_id == self.uom_pack)
        self.assertEqual(pack_line.secondary_uom_ratio, 10.0)
        self.assertIn('Test Pack of 10', pack_line.example_ratio)

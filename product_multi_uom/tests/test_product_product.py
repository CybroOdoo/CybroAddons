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
"""Test suite for product.product extension in product_multi_uom."""
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductProduct(TransactionCase):
    """Test cases for product.product extension with secondary UoM."""

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
            'name': 'Test Pack of 10 Product',
            'relative_uom_id': cls.uom_unit.id,
            'relative_factor': 10.0,
        })

    def test_product_product_create_and_onchange(self):
        """Test creating a product variant automatically triggers _onchange_is_need_secondary_uom."""
        product = self.env['product.product'].create({
            'name': 'Test Variant Multi UoM',
            'uom_id': self.uom_unit.id,
            'is_need_secondary_uom': True,
        })
        secondary_uoms = product.secondary_uom_ids.mapped('secondary_uom_id')
        self.assertIn(self.uom_unit, secondary_uoms)
        self.assertIn(self.uom_pack, secondary_uoms)

        pack_line = product.secondary_uom_ids.filtered(lambda line: line.secondary_uom_id == self.uom_pack)
        self.assertEqual(pack_line.secondary_uom_ratio, 10.0)
        self.assertIn('Test Pack of 10 Product', pack_line.example_ratio)

    def test_product_product_create_without_secondary_uom(self):
        """Test creating a product variant with is_need_secondary_uom=False does not populate lines."""
        product = self.env['product.product'].create({
            'name': 'Test Variant Single UoM',
            'uom_id': self.uom_unit.id,
            'is_need_secondary_uom': False,
        })
        self.assertEqual(len(product.secondary_uom_ids), 0)

    def test_product_product_compute_selected_uom_ids(self):
        """Test _compute_selected_uom_ids on product.product reflects secondary_uom_ids."""
        product = self.env['product.product'].create({
            'name': 'Test Product Selected UoM',
            'uom_id': self.uom_unit.id,
            'is_need_secondary_uom': True,
        })
        self.assertEqual(
            set(product.selected_uom_ids.ids),
            set(product.secondary_uom_ids.mapped('secondary_uom_id.id'))
        )

        product.secondary_uom_ids = [fields.Command.clear()]
        self.assertEqual(len(product.selected_uom_ids), 0)

    def test_product_product_onchange_is_need_secondary_uom_manual(self):
        """Test manually triggering _onchange_is_need_secondary_uom on product variant."""
        product = self.env['product.product'].create({
            'name': 'Test Product Manual Onchange',
            'uom_id': self.uom_unit.id,
            'is_need_secondary_uom': True,
        })
        # Clear existing lines and trigger onchange manually
        product.secondary_uom_ids = [fields.Command.clear()]
        self.assertEqual(len(product.secondary_uom_ids), 0)

        product._onchange_is_need_secondary_uom()
        self.assertTrue(len(product.secondary_uom_ids) >= 2)
        self.assertIn(self.uom_pack, product.secondary_uom_ids.mapped('secondary_uom_id'))

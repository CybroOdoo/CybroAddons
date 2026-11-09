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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestUomProductList(TransactionCase):
    """Test suite for uom.uom product count computation and smart button action."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_primary = cls.env['uom.uom'].create({
            'name': 'Test Primary Box',
        })
        cls.uom_secondary = cls.env['uom.uom'].create({
            'name': 'Test Secondary Pack',
        })
        cls.product_model = cls.env['product.template']

    def test_01_compute_product_count_zero(self):
        """Verify products_uom is 0 when no products are associated with the UOM."""
        self.assertEqual(
            self.uom_primary.products_uom, 0,
            "Newly created UOM with no associated products should have products_uom == 0.",
        )
        self.assertEqual(
            self.uom_secondary.products_uom, 0,
            "Secondary UOM with no associated products should have products_uom == 0.",
        )

    def test_02_compute_product_count_with_products(self):
        """Verify products_uom counts the number of product templates using this UOM."""
        # Create 3 products using uom_primary
        self.product_model.create([
            {'name': 'Test Product 1', 'uom_id': self.uom_primary.id},
            {'name': 'Test Product 2', 'uom_id': self.uom_primary.id},
            {'name': 'Test Product 3', 'uom_id': self.uom_primary.id},
        ])
        # Create 1 product using uom_secondary
        self.product_model.create({
            'name': 'Test Product 4',
            'uom_id': self.uom_secondary.id,
        })

        # Invalidate cache to ensure compute method is triggered
        self.uom_primary.invalidate_recordset(['products_uom'])
        self.uom_secondary.invalidate_recordset(['products_uom'])

        self.assertEqual(
            self.uom_primary.products_uom, 3,
            "Primary UOM should count 3 associated products.",
        )
        self.assertEqual(
            self.uom_secondary.products_uom, 1,
            "Secondary UOM should count 1 associated product.",
        )

    def test_03_compute_product_count_batch(self):
        """Verify compute_product_count functions properly on multi-record recordsets."""
        self.product_model.create([
            {'name': 'Batch Product A', 'uom_id': self.uom_primary.id},
            {'name': 'Batch Product B', 'uom_id': self.uom_secondary.id},
            {'name': 'Batch Product C', 'uom_id': self.uom_secondary.id},
        ])
        uom_records = self.uom_primary | self.uom_secondary
        uom_records._compute_products_uom()

        self.assertEqual(self.uom_primary.products_uom, 1)
        self.assertEqual(self.uom_secondary.products_uom, 2)

    def test_04_action_view_products(self):
        """Verify action_view_products returns the correct action window dictionary."""
        action = self.uom_primary.action_view_products()

        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('name'), 'Products')
        self.assertEqual(action.get('view_mode'), 'kanban,form')
        self.assertEqual(action.get('res_model'), 'product.template')
        self.assertEqual(action.get('domain'), [('uom_id', '=', self.uom_primary.id)])
        self.assertEqual(action.get('context'), "{'create': False}")

        # Verify ensure_one() enforcement on multi-record recordset
        with self.assertRaises(ValueError):
            (self.uom_primary | self.uom_secondary).action_view_products()

    def test_05_product_uom_change_updates_counts(self):
        """Verify updating a product's UOM updates the products_uom count on both UOMs."""
        product = self.product_model.create({
            'name': 'Movable Product',
            'uom_id': self.uom_primary.id,
        })
        self.uom_primary.invalidate_recordset(['products_uom'])
        self.uom_secondary.invalidate_recordset(['products_uom'])
        self.assertEqual(self.uom_primary.products_uom, 1)
        self.assertEqual(self.uom_secondary.products_uom, 0)

        # Move product to secondary UOM
        product.uom_id = self.uom_secondary.id
        self.uom_primary.invalidate_recordset(['products_uom'])
        self.uom_secondary.invalidate_recordset(['products_uom'])

        self.assertEqual(self.uom_primary.products_uom, 0)
        self.assertEqual(self.uom_secondary.products_uom, 1)

    def test_06_uom_form_view_inheritance(self):
        """Verify the inherited form view contains the stat button and products_uom field."""
        view_info = self.env['uom.uom'].get_view(view_type='form')
        arch = view_info.get('arch', '')

        self.assertIn('action_view_products', arch, "Form view must include action_view_products button.")
        self.assertIn('products_uom', arch, "Form view must include products_uom statinfo field.")

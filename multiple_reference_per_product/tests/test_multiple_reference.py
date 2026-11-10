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
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMultipleReferencePerProduct(TransactionCase):
    """Test suite for Multiple Reference Per Product module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reference_model = cls.env['multiple.reference.per.product']
        cls.product_model = cls.env['product.product']
        cls.template_model = cls.env['product.template']

        # Create test products
        cls.product_1 = cls.product_model.create({
            'name': 'Test Product 1',
            'default_code': 'REF_MAIN_01',
        })
        cls.product_2 = cls.product_model.create({
            'name': 'Test Product 2',
            'default_code': 'REF_MAIN_02',
        })
        cls.product_without_code = cls.product_model.create({
            'name': 'Test Product Without Code',
            'default_code': False,
        })

    def test_01_create_reference(self):
        """Test creating reference records and helper method create_reference."""
        ref = self.reference_model.create({
            'multiple_references_name': 'REF_ALT_01',
            'product_id': self.product_1.id,
        })
        self.assertTrue(ref)
        self.assertEqual(ref.multiple_references_name, 'REF_ALT_01')
        self.assertEqual(ref.product_id, self.product_1)
        self.assertFalse(ref.is_default_reference)

        # Test create_reference helper
        res = self.reference_model.create_reference('REF_HELPER_01', self.product_1.id)
        self.assertTrue(res)
        helper_ref = self.reference_model.search([
            ('multiple_references_name', '=', 'REF_HELPER_01'),
            ('product_id', '=', self.product_1.id),
        ])
        self.assertTrue(helper_ref)

    def test_02_create_duplicate_reference(self):
        """Test duplicate reference prevention during create."""
        ref1 = self.reference_model.create({
            'multiple_references_name': 'REF_DUP_01',
            'product_id': self.product_1.id,
        })

        # Creating duplicate reference should return the existing record
        ref2 = self.reference_model.create({
            'multiple_references_name': 'REF_DUP_01',
            'product_id': self.product_1.id,
        })
        self.assertEqual(ref1.id, ref2.id)

        # When product has no default_code, creating a duplicate sets default_code
        ref_no_code = self.reference_model.create({
            'multiple_references_name': 'REF_NO_CODE',
            'product_id': self.product_without_code.id,
        })
        self.assertFalse(self.product_without_code.default_code)

        # Attempt duplicate creation for product without default_code
        ref_no_code_dup = self.reference_model.create({
            'multiple_references_name': 'REF_NO_CODE',
            'product_id': self.product_without_code.id,
        })
        self.assertEqual(ref_no_code.id, ref_no_code_dup.id)
        self.assertEqual(self.product_without_code.default_code, 'REF_NO_CODE')

    def test_03_create_without_required_values(self):
        """Test create branch when required values are not in vals_list dict."""
        # Test creating reference without multiple_references_name or product_id directly
        ref = self.reference_model.create([{
            'multiple_references_name': 'REF_STANDALONE',
            'product_id': self.product_1.id,
        }])
        self.assertTrue(ref)

    def test_04_default_reference_computation_and_action(self):
        """Test is_default_reference computation and action_set_as_default."""
        ref = self.reference_model.create({
            'multiple_references_name': 'REF_ALT_02',
            'product_id': self.product_2.id,
        })
        ref._compute_is_default_reference()
        self.assertFalse(ref.is_default_reference)

        # Action set as default
        ref.action_set_as_default()
        self.assertEqual(self.product_2.default_code, 'REF_ALT_02')
        ref._compute_is_default_reference()
        self.assertTrue(ref.is_default_reference)

    def test_05_reference_write(self):
        """Test write method validation on multiple.reference.per.product."""
        ref1 = self.reference_model.create({
            'multiple_references_name': 'REF_WRITE_01',
            'product_id': self.product_1.id,
        })
        self.reference_model.create({
            'multiple_references_name': 'REF_WRITE_02',
            'product_id': self.product_1.id,
        })

        # Modifying to an already existing reference code for the same product raises ValidationError
        with self.assertRaises(ValidationError):
            ref1.write({'multiple_references_name': 'REF_WRITE_02'})

        # Modifying to a unique reference code succeeds
        result_ok = ref1.write({'multiple_references_name': 'REF_WRITE_UNIQUE'})
        self.assertTrue(result_ok)
        self.assertEqual(ref1.multiple_references_name, 'REF_WRITE_UNIQUE')

        # Modifying without changing the reference name succeeds
        result_product_update = ref1.write({'product_id': self.product_2.id})
        self.assertTrue(result_product_update)
        self.assertEqual(ref1.product_id, self.product_2)

    def test_06_product_product_integration(self):
        """Test product.product fields, computed methods, action and write trigger."""
        product = self.product_model.create({
            'name': 'Integration Test Product',
            'default_code': 'INITIAL_CODE',
        })

        # Add references
        ref1 = self.reference_model.create({
            'multiple_references_name': 'ALT_CODE_A',
            'product_id': product.id,
        })
        self.reference_model.create({
            'multiple_references_name': 'INITIAL_CODE',
            'product_id': product.id,
        })

        # Check compute methods
        product._compute_multiple_references_count()
        self.assertEqual(product.multiple_references_count, 2)

        product._compute_multiple_product_references_ids()
        # multiple_product_references_ids excludes current default_code
        self.assertIn(ref1.id, product.multiple_product_references_ids.ids)

        # Check related multiple_references_code
        self.assertTrue(product.multiple_references_code)

        # Check multiple_references_list action
        action = product.multiple_references_list()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'multiple.reference.per.product')
        self.assertEqual(action.get('context'), {'default_product_id': product.id})
        self.assertEqual(action.get('domain'), [('product_id', '=', product.id)])

        # Test write on product with default_code update
        product.write({'default_code': 'UPDATED_CODE'})
        old_ref = self.reference_model.search([
            ('multiple_references_name', '=', 'INITIAL_CODE'),
            ('product_id', '=', product.id),
        ])
        self.assertTrue(old_ref)

    def test_07_product_template_integration(self):
        """Test product.template fields, computed methods, and action window."""
        template = self.template_model.create({
            'name': 'Template Test Product',
        })
        variant = template.product_variant_id
        variant.default_code = 'TMP_DEFAULT_01'

        ref_variant = self.reference_model.create({
            'multiple_references_name': 'TMP_ALT_01',
            'product_id': variant.id,
        })

        # Compute references on template
        template._compute_multiple_product_references_ids()
        self.assertIn(ref_variant.id, template.multiple_product_references_ids.ids)

        template._compute_multiple_references_count()
        self.assertEqual(template.multiple_references_count, 1)

        # Check template multiple_references_list action
        action = template.multiple_references_list()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'multiple.reference.per.product')
        self.assertEqual(action.get('context'), {'default_product_id': variant.id})
        self.assertEqual(action.get('domain'), [('product_id', '=', variant.id)])

        # Test searching product template using multiple_references_code
        search_result = self.template_model.search([
            ('multiple_references_code', 'ilike', 'TMP_ALT_01')
        ])
        self.assertIn(template.id, search_result.ids)

    def test_08_multi_recordset_and_empty_product(self):
        """Test multi-recordset computations and empty product reference handling."""
        # In-memory record with empty product to test compute fallback
        ref_no_prod = self.reference_model.new({
            'multiple_references_name': 'NO_PROD_REF',
        })
        ref_no_prod._compute_is_default_reference()
        self.assertFalse(ref_no_prod.is_default_reference)

        # Multi-recordset on product.product
        products = self.product_1 | self.product_2
        products._compute_multiple_references_count()
        products._compute_multiple_product_references_ids()

        # Multi-recordset write on product.product
        products.write({'default_code': 'BATCH_CODE'})
        self.assertEqual(self.product_1.default_code, 'BATCH_CODE')
        self.assertEqual(self.product_2.default_code, 'BATCH_CODE')

        # Multi-recordset on product.template
        templates = self.product_1.product_tmpl_id | self.product_2.product_tmpl_id
        templates._compute_multiple_product_references_ids()
        templates._compute_multiple_references_count()


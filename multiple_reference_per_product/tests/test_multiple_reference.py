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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase


class TestMultipleReferencePerProduct(TransactionCase):

    def setUp(self):
        super().setUp()

        # Models
        self.Product = self.env['product.product']
        self.Reference = self.env['multiple.reference.per.product']

        # Create a sample product
        self.product = self.Product.create({
            'name': 'Test Product',
            'default_code': 'REF001',
        })

    def test_create_reference_record(self):
        """Test normal creation of reference"""
        ref = self.Reference.create({
            'multiple_references_name': 'REF002',
            'product_id': self.product.id,
        })
        self.assertTrue(ref)
        self.assertEqual(ref.multiple_references_name, 'REF002')

    def test_duplicate_reference_prevention_create(self):
        """Test duplicate prevention in create"""
        ref1 = self.Reference.create({
            'multiple_references_name': 'REF003',
            'product_id': self.product.id,
        })

        ref2 = self.Reference.create({
            'multiple_references_name': 'REF003',
            'product_id': self.product.id,
        })

        # Should return existing record, not create new one
        self.assertEqual(ref1.id, ref2.id)

    def test_default_reference_computation(self):
        """Test computed field is_default_reference"""
        ref = self.Reference.create({
            'multiple_references_name': 'REF001',
            'product_id': self.product.id,
        })

        ref._is_default_reference()
        self.assertTrue(ref.is_default_reference)

    def test_action_set_as_default(self):
        """Test setting reference as default"""
        ref = self.Reference.create({
            'multiple_references_name': 'REF004',
            'product_id': self.product.id,
        })

        ref.action_set_as_default()
        self.assertEqual(self.product.default_code, 'REF004')

    def test_create_reference_method(self):
        """Test create_reference helper method"""
        result = self.Reference.create_reference(
            'REF005', self.product.id
        )
        self.assertTrue(result)

        ref = self.Reference.search([
            ('multiple_references_name', '=', 'REF005'),
            ('product_id', '=', self.product.id)
        ])
        self.assertTrue(ref)

    def test_write_prevent_duplicate(self):
        """Test write should prevent duplicate references"""
        ref1 = self.Reference.create({
            'multiple_references_name': 'REF006',
            'product_id': self.product.id,
        })

        ref2 = self.Reference.create({
            'multiple_references_name': 'REF007',
            'product_id': self.product.id,
        })

        # Try to update ref2 with duplicate name
        result = ref2.write({
            'multiple_references_name': 'REF006'
        })

        self.assertFalse(result)
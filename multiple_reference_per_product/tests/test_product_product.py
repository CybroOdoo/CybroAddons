from odoo.tests.common import TransactionCase


class TestProductMultipleReference(TransactionCase):

    def setUp(self):
        super().setUp()

        self.Product = self.env['product.product']
        self.Reference = self.env['multiple.reference.per.product']

        # Create product
        self.product = self.Product.create({
            'name': 'Test Product',
            'default_code': 'REF001',
        })

        # Create references
        self.ref1 = self.Reference.create({
            'multiple_references_name': 'REF001',
            'product_id': self.product.id,
        })

        self.ref2 = self.Reference.create({
            'multiple_references_name': 'REF002',
            'product_id': self.product.id,
        })

        self.ref3 = self.Reference.create({
            'multiple_references_name': 'REF003',
            'product_id': self.product.id,
        })

    def test_one2many_relationship(self):
        """Test multiple_references_ids relation"""
        self.assertEqual(len(self.product.multiple_references_ids), 3)

    def test_multiple_references_count(self):
        """Test computed count"""
        self.product._get_multiple_reference_count()
        self.assertEqual(self.product.multiple_references_count, 3)

    def test_multiple_product_references_ids(self):
        """Test computed many2many excluding default_code"""
        self.product._get_multiple_reference()

        result_ids = self.product.multiple_product_references_ids.ids

        # REF001 is default → should be excluded
        self.assertNotIn(self.ref1.id, result_ids)
        self.assertIn(self.ref2.id, result_ids)
        self.assertIn(self.ref3.id, result_ids)

    def test_multiple_references_list_action(self):
        """Test action window output"""
        action = self.product.multiple_references_list()

        self.assertEqual(action['res_model'], 'multiple.reference.per.product')
        self.assertEqual(action['domain'], [('product_id', '=', self.product.id)])
        self.assertEqual(action['context']['default_product_id'], self.product.id)

    def test_write_creates_reference(self):
        """Test write creates old default_code reference"""
        # Change default_code
        self.product.write({
            'default_code': 'NEWREF'
        })

        # Old default_code (REF001) should be added as reference
        ref = self.Reference.search([
            ('multiple_references_name', '=', 'REF001'),
            ('product_id', '=', self.product.id)
        ])

        self.assertTrue(ref)

    def test_write_without_default_code(self):
        """Ensure no reference is created when default_code not changed"""
        initial_count = self.Reference.search_count([
            ('product_id', '=', self.product.id)
        ])

        self.product.write({
            'name': 'Updated Name'
        })

        new_count = self.Reference.search_count([
            ('product_id', '=', self.product.id)
        ])

        self.assertEqual(initial_count, new_count)
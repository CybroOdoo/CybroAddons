# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestMediaCategory(TransactionCase):

    def setUp(self):
        super(TestMediaCategory, self).setUp()
        self.MediaCategory = self.env['media.category']

    def test_create_category(self):
        """Test creating a media category."""
        category = self.MediaCategory.create({'name': 'Test Category'})
        self.assertEqual(category.name, 'Test Category')
